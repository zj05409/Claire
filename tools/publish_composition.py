import hashlib
import json
import re
import shutil
import subprocess
import os
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from tkinter import END, LEFT, Button, Entry, Frame, Label, Listbox, StringVar, Tk, Toplevel, filedialog, messagebox

from PIL import Image
from camera_capture import capture_photo


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "compositions"
COMPOSITIONS_FILE = ROOT / "compositions-data.js"
HTML_FILES = [ROOT / "index.html", ROOT / "composition.html"]


def run(command):
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")


def git_sync():
    result = run(["git", "pull", "--ff-only", "origin", "main"])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def git_publish(message):
    result = run(["git", "add", "compositions-data.js", "index.html", "composition.html", "assets/compositions"])
    if result.returncode:
        raise RuntimeError(result.stderr)
    result = run(["git", "commit", "-m", message])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    result = run(["git", "push", "origin", "main"])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def read_compositions():
    text = COMPOSITIONS_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.CLAIRE_COMPOSITIONS\s*=\s*(\[.*\]);\s*$", text, re.S)
    if not match:
        raise ValueError("无法读取作文数据文件。")
    return json.loads(match.group(1))


def write_compositions(items):
    payload = json.dumps(items, ensure_ascii=False, indent=2)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    COMPOSITIONS_FILE.write_text(
        f'window.CLAIRE_COMPOSITIONS_VERSION = "{stamp}";\n'
        f"window.CLAIRE_COMPOSITIONS = {payload};\n",
        encoding="utf-8",
    )
    for html_file in HTML_FILES:
        text = html_file.read_text(encoding="utf-8")
        text = re.sub(r"compositions-data\.js\?v=[^\"']+", f"compositions-data.js?v={stamp}", text)
        html_file.write_text(text, encoding="utf-8")


def slugify(text):
    normalized = unicodedata.normalize("NFKC", text).strip().lower()
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if ascii_slug:
        return ascii_slug
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"composition-{date.today().isoformat()}-{digest}"


def unique_slug(title, items):
    base = slugify(title)
    existing = {item["slug"] for item in items}
    if base not in existing:
        return base
    return f"{base}-{datetime.now().strftime('%H%M%S')}"


def recognize_title(path):
    paddle_title = recognize_title_with_paddle(path)
    if paddle_title:
        return paddle_title
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    tesseract = next((item for item in candidates if item and Path(item).exists()), None)
    if not tesseract:
        return recognize_title_with_windows_ocr(path)
    temp = ROOT / ".composition-title-crop.png"
    try:
        with Image.open(path) as image:
            image.crop((0, 0, image.width, max(1, image.height // 4))).save(temp)
        result = subprocess.run(
            [tesseract, str(temp), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        lines = [re.sub(r"\s+", "", line) for line in result.stdout.splitlines() if line.strip()]
        return min(lines, key=len)[:40] if lines else ""
    except Exception:
        return ""
    finally:
        temp.unlink(missing_ok=True)


def recognize_title_with_paddle(path):
    package_dir = ROOT / "tools" / "ocr_packages"
    runner = ROOT / "tools" / "paddle_ocr_title.py"
    if not package_dir.exists():
        return ""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_dir)
    env["FLAGS_use_mkldnn"] = "0"
    env["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(
            [sys.executable, str(runner), str(path.resolve())],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        # Paddle may write informational logs to stdout, so parse the final JSON line.
        payload = next(
            (line for line in reversed(result.stdout.splitlines()) if line.strip().startswith("[")),
            "",
        )
        candidates = json.loads(payload) if payload else []
        return choose_paddle_title(candidates)
    except Exception:
        return ""


def choose_paddle_title(candidates):
    filtered = []
    ignored = {"星期", "天气", "修正", "年月日"}
    for item in candidates:
        text = clean_title_line(str(item.get("text", "")))
        score = float(item.get("score", 0))
        box = item.get("box", [0, 0, 0, 0])
        y = box[1] if len(box) > 1 else 99999
        if 2 <= len(text) <= 20 and score >= 0.75 and text not in ignored:
            filtered.append((y, -score, len(text), text))
    if not filtered:
        return ""
    # The title appears before body text and is usually a short, high-confidence line.
    filtered.sort()
    top_area = filtered[:5]
    return min(top_area, key=lambda item: (item[2], item[1]))[3]


def recognize_title_with_windows_ocr(path):
    temp = ROOT / ".composition-title-crop.png"
    try:
        with Image.open(path) as image:
            # The title is normally centered near the top of the first page.
            top = image.crop((0, 0, image.width, max(1, image.height // 4)))
            top.save(temp)
        script = ROOT / "tools" / "windows_ocr.ps1"
        result = subprocess.run(
            [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(script), "-ImagePath", str(temp.resolve()),
            ],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=45,
        )
        lines = [clean_title_line(line) for line in result.stdout.splitlines()]
        lines = [line for line in lines if line]
        return choose_title_line(lines)
    except Exception:
        return ""
    finally:
        temp.unlink(missing_ok=True)


def clean_title_line(line):
    line = re.sub(r"\s+", "", line)
    line = re.sub(r"^[年月日星期天气：:]+$", "", line)
    line = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9《》·]", "", line)
    return line[:40]


def choose_title_line(lines):
    candidates = [
        line for line in lines
        if 2 <= len(line) <= 20 and not re.fullmatch(r"[年月日星期天气]+", line)
    ]
    if not candidates:
        return ""
    # Titles are usually short and appear before the body text.
    return min(candidates[:5], key=len)


def suggested_title(path):
    ocr_title = recognize_title(path)
    if ocr_title:
        return ocr_title
    name = path.stem
    name = re.sub(r"^(微信图片|img|image|photo)[_-]*", "", name, flags=re.I)
    name = re.sub(r"[_-]?\d{8,}.*$", "", name)
    return name.strip(" _-") or "新作文"


def stitch(paths, output):
    images = []
    try:
        images = [Image.open(path).convert("RGB") for path in paths]
        width = min(image.width for image in images)
        resized = [
            image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
            for image in images
        ]
        result = Image.new("RGB", (width, sum(image.height for image in resized)), "white")
        y = 0
        for image in resized:
            result.paste(image, (0, y))
            y += image.height
        result.save(output, quality=94, optimize=True)
        result.close()
        for image in resized:
            image.close()
    finally:
        for image in images:
            image.close()


class Publisher:
    def __init__(self):
        self.root = Tk()
        self.root.title("Claire 作文发布与管理工具")
        self.root.geometry("820x560")
        self.paths = []
        self.title = StringVar()
        self.rotation_degrees = 90
        self.rotation_text = StringVar(value=f"旋转角度：{self.rotation_degrees}°")
        self.status = StringVar(value="请选择两张或更多作文照片。")

        Label(self.root, text="Claire 作文发布与管理工具", font=("Microsoft YaHei", 20, "bold")).pack(pady=(22, 5))
        Label(self.root, text="自动拼接、发布和删除 GitHub 上的公开作文", fg="#8e6578").pack()

        title_frame = Frame(self.root)
        title_frame.pack(fill="x", padx=28, pady=(20, 10))
        Label(title_frame, text="作文标题：", font=("Microsoft YaHei", 10, "bold")).pack(side=LEFT)
        Entry(title_frame, textvariable=self.title, font=("Microsoft YaHei", 11)).pack(side=LEFT, fill="x", expand=True)

        self.listbox = Listbox(self.root, font=("Microsoft YaHei", 10), height=12)
        self.listbox.pack(fill="both", expand=True, padx=28, pady=8)

        controls = Frame(self.root)
        controls.pack(pady=8)
        Button(controls, text="选择照片", command=self.choose).pack(side=LEFT, padx=4)
        Button(controls, text="拍照添加", command=self.take_photo).pack(side=LEFT, padx=4)
        Button(controls, textvariable=self.rotation_text, command=self.rotate_capture).pack(side=LEFT, padx=4)
        Button(controls, text="上移", command=lambda: self.move(-1)).pack(side=LEFT, padx=4)
        Button(controls, text="下移", command=lambda: self.move(1)).pack(side=LEFT, padx=4)
        Button(controls, text="移除照片", command=self.remove_photo).pack(side=LEFT, padx=4)

        Label(self.root, textvariable=self.status, fg="#8e6578", wraplength=670).pack(pady=8)
        actions = Frame(self.root)
        actions.pack(pady=(4, 22))
        Button(
            actions, text="自动拼接并发布", command=self.publish, bg="#d85f91", fg="white",
            font=("Microsoft YaHei", 11, "bold"), padx=22, pady=9
        ).pack(side=LEFT, padx=7)
        Button(
            actions, text="删除已发布作文", command=self.open_delete_window, bg="#9c486c", fg="white",
            font=("Microsoft YaHei", 11, "bold"), padx=22, pady=9
        ).pack(side=LEFT, padx=7)

    def refresh(self):
        self.listbox.delete(0, END)
        for index, path in enumerate(self.paths, 1):
            self.listbox.insert(END, f"{index}. {path.name}")
        self.status.set(f"已选择 {len(self.paths)} 张照片。发布前请确认顺序和标题。")

    def choose(self):
        selected = filedialog.askopenfilenames(
            title="选择两张或更多作文照片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.webp"), ("所有文件", "*.*")],
        )
        if not selected:
            return
        self.paths = [Path(path) for path in selected]
        if not self.title.get().strip():
            recognized = suggested_title(self.paths[0])
            self.title.set(recognized)
        self.refresh()
        self.status.set(f"已自动识别建议标题“{self.title.get()}”。请确认；不正确时直接修改。")

    def take_photo(self):
        try:
            captured = capture_photo(
                "composition",
                rotate_degrees=self.rotation_degrees,
                camera_indexes=[0, 1, 2, 3, 4],
                remember_camera=False,
            )
        except Exception as error:
            messagebox.showerror("拍照失败", str(error))
            return
        self.paths.append(captured)
        if not self.title.get().strip():
            self.title.set(suggested_title(captured))
        self.refresh()
        self.status.set(f"已拍照并添加：{captured.name}。可以继续拍下一张，或确认顺序后发布。")

    def rotate_capture(self):
        self.rotation_degrees = (self.rotation_degrees + 90) % 360
        self.rotation_text.set(f"旋转角度：{self.rotation_degrees}°")
        self.status.set(f"下一次拍照会旋转 {self.rotation_degrees}°。")

    def move(self, offset):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        target = index + offset
        if 0 <= target < len(self.paths):
            self.paths[index], self.paths[target] = self.paths[target], self.paths[index]
            self.refresh()
            self.listbox.selection_set(target)

    def remove_photo(self):
        selected = self.listbox.curselection()
        if selected:
            self.paths.pop(selected[0])
            self.refresh()

    def publish(self):
        title = self.title.get().strip()
        if len(self.paths) < 2:
            messagebox.showerror("无法发布", "请至少选择两张作文照片。")
            return
        if not title:
            messagebox.showerror("无法发布", "请确认作文标题。")
            return
        try:
            git_sync()
            items = read_compositions()
            slug = unique_slug(title, items)
            ASSET_DIR.mkdir(parents=True, exist_ok=True)
            for index, source in enumerate(self.paths, 1):
                suffix = source.suffix.lower() if source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
                shutil.copy2(source, ASSET_DIR / f"{slug}-{index}{suffix}")
            stitched = ASSET_DIR / f"{slug}.jpg"
            stitch(self.paths, stitched)
            items.insert(0, {
                "slug": slug,
                "title": title,
                "date": date.today().isoformat(),
                "summary": "点击进入详情页，查看完整作文。",
                "image": f"assets/compositions/{stitched.name}",
            })
            write_compositions(items)
            git_publish(f"Publish composition: {title}")
        except Exception as error:
            messagebox.showerror("发布失败", str(error))
            return
        messagebox.showinfo("发布成功", f"《{title}》已推送到 GitHub。\n\n网站通常会在1至3分钟内自动更新。")
        self.paths = []
        self.title.set("")
        self.refresh()

    def open_delete_window(self):
        try:
            git_sync()
            items = read_compositions()
        except Exception as error:
            messagebox.showerror("读取失败", str(error))
            return
        window = Toplevel(self.root)
        window.title("删除已发布作文")
        window.geometry("560x420")
        Label(window, text="选择要从 GitHub 和网站删除的作文", font=("Microsoft YaHei", 14, "bold")).pack(pady=16)
        listing = Listbox(window, font=("Microsoft YaHei", 11))
        listing.pack(fill="both", expand=True, padx=24, pady=8)
        for item in items:
            listing.insert(END, f"{item['title']}  ·  {item.get('date', '')}")

        def confirm_delete():
            selection = listing.curselection()
            if not selection:
                messagebox.showwarning("尚未选择", "请先选择一篇作文。", parent=window)
                return
            item = items[selection[0]]
            if not messagebox.askyesno("确认删除", f"确定永久删除《{item['title']}》吗？", parent=window):
                return
            try:
                for path in ASSET_DIR.glob(f"{item['slug']}*"):
                    path.unlink()
                items.remove(item)
                write_compositions(items)
                git_publish(f"Delete composition: {item['title']}")
            except Exception as error:
                messagebox.showerror("删除失败", str(error), parent=window)
                return
            messagebox.showinfo("删除成功", f"《{item['title']}》已从 GitHub 删除。", parent=window)
            window.destroy()

        Button(window, text="删除选中的作文", command=confirm_delete, bg="#9c486c", fg="white", padx=18, pady=8).pack(pady=15)

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    Publisher().start()

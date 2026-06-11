import json
import hashlib
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path
from tkinter import END, LEFT, RIGHT, Button, Entry, Frame, Label, Listbox, StringVar, Tk, filedialog, messagebox

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "compositions"
DATA_FILE = ROOT / "data.js"
PYTHON = sys.executable


def run(command):
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")


def slugify(text):
    normalized = unicodedata.normalize("NFKC", text).strip().lower()
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if ascii_slug:
        return ascii_slug
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"composition-{date.today().isoformat()}-{digest}"


def suggested_title(path):
    ocr_title = recognize_title(path)
    if ocr_title:
        return ocr_title
    name = path.stem
    name = re.sub(r"^(微信图片|img|image|photo)[_-]*", "", name, flags=re.I)
    name = re.sub(r"[_-]?\d{8,}.*$", "", name)
    return name.strip(" _-") or "新作文"


def recognize_title(path):
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    tesseract = next((item for item in candidates if item and Path(item).exists()), None)
    if not tesseract:
        return ""
    try:
        with Image.open(path) as image:
            top = image.crop((0, 0, image.width, max(1, image.height // 4)))
            temp = ROOT / ".composition-title-crop.png"
            top.save(temp)
        result = subprocess.run(
            [tesseract, str(temp), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        temp.unlink(missing_ok=True)
        lines = [re.sub(r"\s+", "", line) for line in result.stdout.splitlines() if line.strip()]
        return min(lines, key=len)[:40] if lines else ""
    except Exception:
        return ""


def stitch(paths, output):
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


def add_to_data(title, slug, image_path):
    text = DATA_FILE.read_text(encoding="utf-8")
    if f'slug: "{slug}"' in text:
        raise ValueError(f"网站中已存在标识为 {slug} 的作文。")
    entry = {
        "slug": slug,
        "title": title,
        "date": date.today().isoformat(),
        "summary": "点击进入详情页，查看完整作文。",
        "image": image_path,
    }
    lines = [
        "    {",
        f'      slug: {json.dumps(entry["slug"], ensure_ascii=False)},',
        f'      title: {json.dumps(entry["title"], ensure_ascii=False)},',
        f'      date: {json.dumps(entry["date"], ensure_ascii=False)},',
        f'      summary: {json.dumps(entry["summary"], ensure_ascii=False)},',
        f'      image: {json.dumps(entry["image"], ensure_ascii=False)}',
        "    },",
    ]
    marker = "  compositions: [\n"
    if marker not in text:
        raise ValueError("无法找到 data.js 中的作文列表。")
    DATA_FILE.write_text(text.replace(marker, marker + "\n".join(lines) + "\n", 1), encoding="utf-8")


class Publisher:
    def __init__(self):
        self.root = Tk()
        self.root.title("Claire 作文一键发布工具")
        self.root.geometry("720x520")
        self.paths = []
        self.title = StringVar()
        self.status = StringVar(value="请选择两张或更多作文照片。")

        Label(self.root, text="Claire 作文一键发布工具", font=("Microsoft YaHei", 20, "bold")).pack(pady=(22, 5))
        Label(self.root, text="选择照片 → 确认标题 → 自动拼接并发布到 GitHub", fg="#8e6578").pack()

        title_frame = Frame(self.root)
        title_frame.pack(fill="x", padx=28, pady=(20, 10))
        Label(title_frame, text="作文标题：", font=("Microsoft YaHei", 10, "bold")).pack(side=LEFT)
        Entry(title_frame, textvariable=self.title, font=("Microsoft YaHei", 11)).pack(side=LEFT, fill="x", expand=True)

        self.listbox = Listbox(self.root, font=("Microsoft YaHei", 10), height=12)
        self.listbox.pack(fill="both", expand=True, padx=28, pady=8)

        controls = Frame(self.root)
        controls.pack(pady=8)
        Button(controls, text="选择照片", command=self.choose).pack(side=LEFT, padx=4)
        Button(controls, text="上移", command=lambda: self.move(-1)).pack(side=LEFT, padx=4)
        Button(controls, text="下移", command=lambda: self.move(1)).pack(side=LEFT, padx=4)
        Button(controls, text="删除", command=self.remove).pack(side=LEFT, padx=4)

        Label(self.root, textvariable=self.status, fg="#8e6578", wraplength=650).pack(pady=8)
        Button(
            self.root,
            text="自动拼接并发布到 GitHub",
            command=self.publish,
            bg="#d85f91",
            fg="white",
            font=("Microsoft YaHei", 11, "bold"),
            padx=22,
            pady=9,
        ).pack(pady=(4, 22))

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
            self.title.set(suggested_title(self.paths[0]))
        self.refresh()

    def move(self, offset):
        selected = self.listbox.curselection()
        if not selected:
            return
        index = selected[0]
        target = index + offset
        if target < 0 or target >= len(self.paths):
            return
        self.paths[index], self.paths[target] = self.paths[target], self.paths[index]
        self.refresh()
        self.listbox.selection_set(target)

    def remove(self):
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
        slug = slugify(title)
        ASSET_DIR.mkdir(parents=True, exist_ok=True)
        originals = []
        try:
            for index, source in enumerate(self.paths, 1):
                suffix = source.suffix.lower() if source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
                destination = ASSET_DIR / f"{slug}-{index}{suffix}"
                shutil.copy2(source, destination)
                originals.append(destination)
            stitched = ASSET_DIR / f"{slug}.jpg"
            stitch(self.paths, stitched)
            add_to_data(title, slug, f"assets/compositions/{stitched.name}")

            result = run(["git", "add", "data.js", "assets/compositions"])
            if result.returncode:
                raise RuntimeError(result.stderr)
            result = run(["git", "commit", "-m", f"Publish composition: {title}"])
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            result = run(["git", "push", "origin", "main"])
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
        except Exception as error:
            messagebox.showerror("发布失败", str(error))
            return
        messagebox.showinfo(
            "发布成功",
            f"《{title}》已拼接并推送到 GitHub。\n\n网站通常会在1至3分钟内自动更新。",
        )
        self.paths = []
        self.title.set("")
        self.refresh()

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    Publisher().start()

import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from datetime import date, datetime
from pathlib import Path
from tkinter import END, LEFT, Button, Entry, Frame, Label, Listbox, StringVar, Text, Tk, Toplevel, filedialog, messagebox

from camera_capture import _crop_black_borders, _load_cv2, _save_frame, capture_photo

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "artworks"
ARTWORKS_FILE = ROOT / "artworks-data.js"
INDEX_FILE = ROOT / "index.html"


def run(command):
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")


def git_sync():
    result = run(["git", "pull", "--ff-only", "origin", "main"])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def git_publish(message):
    result = run(["git", "add", "artworks-data.js", "index.html", "assets/artworks"])
    if result.returncode:
        raise RuntimeError(result.stderr)
    result = run(["git", "commit", "-m", message])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    result = run(["git", "push", "origin", "main"])
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def read_artworks():
    text = ARTWORKS_FILE.read_text(encoding="utf-8")
    match = re.search(r"window\.CLAIRE_ARTWORKS\s*=\s*(\[.*\]);\s*$", text, re.S)
    if not match:
        raise ValueError("无法读取画作数据文件。")
    return json.loads(match.group(1))


def write_artworks(items):
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ARTWORKS_FILE.write_text(
        f'window.CLAIRE_ARTWORKS_VERSION = "{stamp}";\n'
        f"window.CLAIRE_ARTWORKS = {json.dumps(items, ensure_ascii=False, indent=2)};\n",
        encoding="utf-8",
    )
    text = INDEX_FILE.read_text(encoding="utf-8")
    text = re.sub(r"artworks-data\.js\?v=[^\"']+", f"artworks-data.js?v={stamp}", text)
    INDEX_FILE.write_text(text, encoding="utf-8")


def slugify(text):
    normalized = unicodedata.normalize("NFKC", text).strip().lower()
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if ascii_slug:
        return ascii_slug
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"artwork-{date.today().isoformat()}-{digest}"


def unique_slug(title, items):
    base = slugify(title)
    existing = {item["slug"] for item in items}
    return base if base not in existing else f"{base}-{datetime.now().strftime('%H%M%S')}"


def suggested_title(path):
    name = path.stem
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"^(微信图片|img|image|photo|drawing|artwork|screenshot|capture)[_\-\s]*", "", name, flags=re.I)
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" _-") or "新画作"


def prepare_artwork_image(source, destination):
    cv2 = _load_cv2()
    image = cv2.imread(str(source))
    if image is None:
        shutil.copy2(source, destination)
        return
    image = _crop_black_borders(cv2, image)
    _save_frame(cv2, image, destination)


class ArtworkPublisher:
    def __init__(self):
        self.root = Tk()
        self.root.title("Claire 画作发布与管理工具")
        self.root.geometry("720x560")
        self.image_path = None
        self.title = StringVar()
        self.status = StringVar(value="请选择一张画作图片。")

        Label(self.root, text="Claire 画作发布与管理工具", font=("Microsoft YaHei", 20, "bold")).pack(pady=(22, 5))
        Label(self.root, text="发布画作到“我的画作”栏目，或删除已发布画作", fg="#8e6578").pack()
        title_frame = Frame(self.root)
        title_frame.pack(fill="x", padx=28, pady=(22, 10))
        Label(title_frame, text="画作名称：", font=("Microsoft YaHei", 10, "bold")).pack(side=LEFT)
        Entry(title_frame, textvariable=self.title, font=("Microsoft YaHei", 11)).pack(side=LEFT, fill="x", expand=True)
        Label(self.root, text="画作介绍（可选）：", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=28)
        self.summary = Text(self.root, font=("Microsoft YaHei", 10), height=6)
        self.summary.pack(fill="x", padx=28, pady=(6, 12))
        Label(self.root, textvariable=self.status, fg="#8e6578", wraplength=650).pack(pady=8)
        image_actions = Frame(self.root)
        image_actions.pack(pady=5)
        Button(image_actions, text="选择画作图片", command=self.choose_image, padx=18, pady=7).pack(side=LEFT, padx=5)
        Button(image_actions, text="拍照选择画作", command=self.take_photo, padx=18, pady=7).pack(side=LEFT, padx=5)
        actions = Frame(self.root)
        actions.pack(pady=20)
        Button(actions, text="发布到 GitHub", command=self.publish, bg="#d85f91", fg="white",
               font=("Microsoft YaHei", 11, "bold"), padx=24, pady=9).pack(side=LEFT, padx=7)
        Button(actions, text="删除已发布画作", command=self.open_delete_window, bg="#9c486c", fg="white",
               font=("Microsoft YaHei", 11, "bold"), padx=24, pady=9).pack(side=LEFT, padx=7)

    def choose_image(self):
        selected = filedialog.askopenfilename(
            title="选择画作图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.webp"), ("所有文件", "*.*")],
        )
        if not selected:
            return
        self.image_path = Path(selected)
        self.title.set(suggested_title(self.image_path))
        self.status.set(f"已从文件名提取标题：{self.title.get()}。不正确时可以直接修改。")

    def take_photo(self):
        try:
            captured = capture_photo("artwork")
        except Exception as error:
            messagebox.showerror("拍照失败", str(error))
            return
        self.image_path = captured
        if not self.title.get().strip():
            self.title.set(suggested_title(captured))
        self.status.set(f"已拍照并选择：{captured.name}。请确认名称和介绍后发布。")

    def publish(self):
        title = self.title.get().strip()
        summary = self.summary.get("1.0", END).strip() or "Claire 的画作。"
        if not self.image_path:
            messagebox.showerror("无法发布", "请先选择画作图片。")
            return
        if not title:
            messagebox.showerror("无法发布", "请填写画作名称。")
            return
        try:
            git_sync()
            items = read_artworks()
            slug = unique_slug(title, items)
            ASSET_DIR.mkdir(parents=True, exist_ok=True)
            destination = ASSET_DIR / f"{slug}.jpg"
            prepare_artwork_image(self.image_path, destination)
            items.insert(0, {"slug": slug, "title": title, "date": date.today().isoformat(),
                             "summary": summary, "image": f"assets/artworks/{destination.name}"})
            write_artworks(items)
            git_publish(f"Publish artwork: {title}")
        except Exception as error:
            messagebox.showerror("发布失败", str(error))
            return
        messagebox.showinfo("发布成功", f"《{title}》已推送到 GitHub。\n\n网站通常会在1至3分钟内自动更新。")
        self.image_path = None
        self.title.set("")
        self.summary.delete("1.0", END)
        self.status.set("请选择下一张画作图片。")

    def open_delete_window(self):
        try:
            git_sync()
            items = read_artworks()
        except Exception as error:
            messagebox.showerror("读取失败", str(error))
            return
        window = Toplevel(self.root)
        window.title("删除已发布画作")
        window.geometry("560x420")
        Label(window, text="选择要从 GitHub 和网站删除的画作", font=("Microsoft YaHei", 14, "bold")).pack(pady=16)
        listing = Listbox(window, font=("Microsoft YaHei", 11))
        listing.pack(fill="both", expand=True, padx=24, pady=8)
        for item in items:
            listing.insert(END, f"{item['title']}  ·  {item.get('date', '')}")

        def confirm_delete():
            selection = listing.curselection()
            if not selection:
                messagebox.showwarning("尚未选择", "请先选择一幅画作。", parent=window)
                return
            item = items[selection[0]]
            if not messagebox.askyesno("确认删除", f"确定永久删除《{item['title']}》吗？", parent=window):
                return
            try:
                (ROOT / item["image"]).unlink(missing_ok=True)
                items.remove(item)
                write_artworks(items)
                git_publish(f"Delete artwork: {item['title']}")
            except Exception as error:
                messagebox.showerror("删除失败", str(error), parent=window)
                return
            messagebox.showinfo("删除成功", f"《{item['title']}》已从 GitHub 删除。", parent=window)
            window.destroy()

        Button(window, text="删除选中的画作", command=confirm_delete, bg="#9c486c", fg="white", padx=18, pady=8).pack(pady=15)

    def start(self):
        self.root.mainloop()


if __name__ == "__main__":
    ArtworkPublisher().start()

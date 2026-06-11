const content = window.CLAIRE_CONTENT;

const sections = [
  { id: "compositions", title: "我的作文", eyebrow: "WRITING", empty: "第一篇作文正在路上。", type: "作文" },
  { id: "artworks", title: "我的画作", eyebrow: "ARTWORKS", empty: "第一幅画作正在路上。", type: "画作" },
  { id: "projects", title: "编程作品", eyebrow: "CODING", empty: "第一个编程作品正在路上。", type: "编程作品" },
  { id: "books", title: "读过的书", eyebrow: "BOOKSHELF", empty: "阅读记录正在路上。", type: "书籍" },
  { id: "movies", title: "看过的电影", eyebrow: "MOVIES", empty: "电影记录正在路上。", type: "电影" },
  { id: "games", title: "玩过的桌游与电子游戏", eyebrow: "GAMES", empty: "游戏记录正在路上。", type: "游戏" },
];

const collections = document.querySelector("#collections");
const dialog = document.querySelector("#detail-dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogMeta = document.querySelector("#dialog-meta");
const dialogContent = document.querySelector("#dialog-content");
const dialogImage = document.querySelector("#dialog-image");
let localCompositions = [];
let compositionFiles = [];
let stitchedBlob = null;
let stitchedPreviewUrl = "";

function showDetail(item, type) {
  dialogMeta.textContent = [type, item.kind, item.date, item.creator].filter(Boolean).join(" · ");
  dialogTitle.textContent = item.title;
  dialogContent.textContent = item.content || item.summary || "暂时没有更多介绍。";
  dialogImage.hidden = !item.image;
  if (item.image) {
    dialogImage.src = item.image;
    dialogImage.alt = item.title;
  }
  dialog.showModal();
}

function card(item, type, local = false) {
  const article = document.createElement("article");
  article.className = `item-card${local ? " saved-composition" : ""}`;
  if (item.image) {
    const image = document.createElement("img");
    image.src = item.image;
    image.alt = item.title;
    article.append(image);
  }
  const body = document.createElement("div");
  body.className = "card-body";
  const meta = document.createElement("p");
  meta.className = "card-meta";
  meta.textContent = [type, item.kind, item.date, item.creator].filter(Boolean).join(" · ");
  const title = document.createElement("h3");
  title.textContent = item.title;
  const summary = document.createElement("p");
  summary.textContent = item.summary || "等待补充介绍。";
  body.append(meta, title, summary);

  if (item.link) {
    const link = document.createElement("a");
    link.href = item.link;
    link.textContent = "打开作品 →";
    body.append(link);
  } else {
    const button = document.createElement("button");
    button.textContent = "查看详情";
    button.addEventListener("click", () => showDetail(item, type));
    body.append(button);
  }
  if (local) {
    const remove = document.createElement("button");
    remove.className = "delete-composition";
    remove.textContent = "从这台设备删除";
    remove.addEventListener("click", async () => {
      if (!window.confirm(`确定删除作文《${item.title}》吗？`)) return;
      await deleteComposition(item.id);
      await refreshLocalCompositions();
    });
    body.append(remove);
  }
  article.append(body);
  return article;
}

function renderCompositionGrid() {
  const grid = document.querySelector("#compositions .grid");
  const count = document.querySelector("#compositions .section-heading span");
  if (!grid) return;
  grid.replaceChildren();
  const all = [...localCompositions, ...content.compositions];
  count.textContent = `${all.length} 条记录`;
  if (!all.length) {
    grid.innerHTML = `<div class="empty"><strong>这里暂时是空的</strong><p>第一篇作文正在路上。</p></div>`;
    return;
  }
  localCompositions.forEach((item) => grid.append(card(item, "作文", true)));
  content.compositions.forEach((item) => grid.append(card(item, "作文")));
}

function createUploader() {
  const wrap = document.createElement("div");
  wrap.className = "composition-uploader";
  wrap.innerHTML = `
    <div class="uploader-layout">
      <div class="upload-panel">
        <input id="composition-title" class="composition-title" maxlength="80" placeholder="手动输入作文标题">
        <label class="file-picker" for="composition-images">
          <strong>选择两张或更多作文照片</strong>
          <span>系统会按选择顺序，自动统一宽度并从上往下拼接</span>
        </label>
        <input id="composition-images" type="file" accept="image/*" multiple>
        <p id="upload-message" class="upload-message" role="status">尚未选择照片。</p>
        <ol id="image-order" class="image-order"></ol>
        <button id="save-composition" class="tool-button" disabled>添加到我的作文</button>
        <p class="local-note">作文保存在当前设备的浏览器中，不会自动同步到其他设备。</p>
      </div>
      <div class="preview-panel">
        <div id="preview-placeholder"><strong>自动拼接预览</strong><span>选择至少两张照片后，系统会自动生成。</span></div>
        <canvas id="composition-canvas"></canvas>
      </div>
    </div>`;
  return wrap;
}

sections.forEach(({ id, title, eyebrow, empty, type }) => {
  const section = document.createElement("section");
  section.id = id;
  section.className = "collection section";
  section.innerHTML = `<div class="section-heading"><div><p class="kicker">${eyebrow}</p><h2>${title}</h2></div><span>${content[id].length} 条记录</span></div>`;
  if (id === "compositions") section.append(createUploader());
  const grid = document.createElement("div");
  grid.className = "grid";
  if (!content[id].length) grid.innerHTML = `<div class="empty"><strong>这里暂时是空的</strong><p>${empty}</p></div>`;
  else content[id].forEach((item) => grid.append(card(item, type)));
  section.append(grid);
  collections.append(section);
});

document.querySelector("#work-count").textContent =
  content.compositions.length + content.artworks.length + content.projects.length;
document.querySelector("#book-count").textContent = content.books.length;
document.querySelector("#experience-count").textContent = content.movies.length + content.games.length;

document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

const nav = document.querySelector("#nav");
document.querySelector("#menu-button").addEventListener("click", () => nav.classList.toggle("open"));
nav.addEventListener("click", () => nav.classList.remove("open"));

const imageInput = document.querySelector("#composition-images");
const titleInput = document.querySelector("#composition-title");
const imageOrder = document.querySelector("#image-order");
const uploadMessage = document.querySelector("#upload-message");
const saveButton = document.querySelector("#save-composition");
const compositionCanvas = document.querySelector("#composition-canvas");
const previewPlaceholder = document.querySelector("#preview-placeholder");

function setUploadMessage(message, isError = false) {
  uploadMessage.textContent = message;
  uploadMessage.classList.toggle("error", isError);
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    const url = URL.createObjectURL(file);
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error(`无法读取 ${file.name}`));
    };
    image.src = url;
  });
}

function renderImageOrder() {
  imageOrder.replaceChildren();
  compositionFiles.forEach((file, index) => {
    const item = document.createElement("li");
    const thumb = document.createElement("img");
    const info = document.createElement("div");
    const name = document.createElement("strong");
    const position = document.createElement("span");
    const controls = document.createElement("div");
    controls.className = "order-buttons";
    thumb.src = URL.createObjectURL(file);
    thumb.onload = () => URL.revokeObjectURL(thumb.src);
    thumb.alt = `第${index + 1}张照片`;
    name.textContent = file.name;
    position.textContent = `第 ${index + 1} 张`;
    info.append(name, position);
    [["↑", -1, "上移"], ["↓", 1, "下移"], ["×", 0, "删除"]].forEach(([text, offset, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = text;
      button.title = label;
      button.setAttribute("aria-label", `${file.name}${label}`);
      button.disabled = (offset === -1 && index === 0) || (offset === 1 && index === compositionFiles.length - 1);
      button.addEventListener("click", async () => {
        if (offset === 0) compositionFiles.splice(index, 1);
        else [compositionFiles[index], compositionFiles[index + offset]] = [compositionFiles[index + offset], compositionFiles[index]];
        await updateUploader();
      });
      controls.append(button);
    });
    item.append(thumb, info, controls);
    imageOrder.append(item);
  });
}

function canvasToBlob(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("无法生成拼接图片。")), "image/jpeg", 0.92);
  });
}

async function autoStitch() {
  if (compositionFiles.length < 2) {
    stitchedBlob = null;
    compositionCanvas.style.display = "none";
    previewPlaceholder.style.display = "grid";
    saveButton.disabled = true;
    return;
  }
  setUploadMessage("正在自动统一宽度并拼接照片……");
  try {
    const images = await Promise.all(compositionFiles.map(loadImage));
    const targetWidth = Math.min(...images.map((image) => image.naturalWidth));
    const heights = images.map((image) => Math.round(image.naturalHeight * targetWidth / image.naturalWidth));
    const totalHeight = heights.reduce((sum, height) => sum + height, 0);
    if (targetWidth * totalHeight > 70_000_000 || targetWidth > 32767 || totalHeight > 32767) {
      throw new Error("拼接图片太大，请先降低照片分辨率后重试。");
    }
    compositionCanvas.width = targetWidth;
    compositionCanvas.height = totalHeight;
    const context = compositionCanvas.getContext("2d");
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, targetWidth, totalHeight);
    let y = 0;
    images.forEach((image, index) => {
      context.drawImage(image, 0, y, targetWidth, heights[index]);
      y += heights[index];
    });
    stitchedBlob = await canvasToBlob(compositionCanvas);
    previewPlaceholder.style.display = "none";
    compositionCanvas.style.display = "block";
    saveButton.disabled = !titleInput.value.trim();
    setUploadMessage(`自动拼接完成：共 ${images.length} 张照片，统一宽度 ${targetWidth}px。`);
  } catch (error) {
    stitchedBlob = null;
    saveButton.disabled = true;
    setUploadMessage(error.message || "拼接失败，请重新选择照片。", true);
  }
}

async function updateUploader() {
  renderImageOrder();
  if (!compositionFiles.length) setUploadMessage("尚未选择照片。");
  else if (compositionFiles.length < 2) setUploadMessage("还需要至少选择一张照片。", true);
  await autoStitch();
}

imageInput.addEventListener("change", async () => {
  compositionFiles = [...imageInput.files].filter((file) => file.type.startsWith("image/"));
  await updateUploader();
});

titleInput.addEventListener("input", () => {
  saveButton.disabled = !stitchedBlob || !titleInput.value.trim();
});

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("claire-personal-site", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("compositions", { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function runStore(mode, action) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction("compositions", mode);
    const store = transaction.objectStore("compositions");
    action(store, resolve, reject);
    transaction.onerror = () => reject(transaction.error);
    transaction.oncomplete = () => db.close();
  });
}

function saveComposition(record) {
  return runStore("readwrite", (store, resolve, reject) => {
    const request = store.put(record);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

function getCompositions() {
  return runStore("readonly", (store, resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function deleteComposition(id) {
  return runStore("readwrite", (store, resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function refreshLocalCompositions() {
  localCompositions.forEach((item) => item.image && URL.revokeObjectURL(item.image));
  const stored = await getCompositions();
  localCompositions = stored.sort((a, b) => b.createdAt - a.createdAt).map((item) => ({
    ...item,
    date: new Date(item.createdAt).toLocaleDateString("zh-CN"),
    summary: `${item.photoCount} 张作文照片自动拼接`,
    image: URL.createObjectURL(item.imageBlob),
  }));
  renderCompositionGrid();
  document.querySelector("#work-count").textContent =
    content.compositions.length + content.artworks.length + content.projects.length + localCompositions.length;
}

saveButton.addEventListener("click", async () => {
  const title = titleInput.value.trim();
  if (!title || !stitchedBlob) return;
  saveButton.disabled = true;
  setUploadMessage("正在保存作文……");
  try {
    await saveComposition({
      id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`,
      title,
      imageBlob: stitchedBlob,
      photoCount: compositionFiles.length,
      createdAt: Date.now(),
    });
    titleInput.value = "";
    imageInput.value = "";
    compositionFiles = [];
    stitchedBlob = null;
    compositionCanvas.style.display = "none";
    previewPlaceholder.style.display = "grid";
    renderImageOrder();
    setUploadMessage("作文已经添加到“我的作文”区域。");
    await refreshLocalCompositions();
  } catch {
    setUploadMessage("保存失败，可能是浏览器存储空间不足。", true);
    saveButton.disabled = false;
  }
});

refreshLocalCompositions().catch(() => setUploadMessage("无法读取这台设备上保存的作文。", true));

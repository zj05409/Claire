const content = window.CLAIRE_CONTENT;
const UPLOAD_PASSWORD_HASH = "0567920039296b530fe17199dea7b78bdbb8fe5b40dcda33f715090f1df5f2a3";

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
let compositionFiles = [];
let stitchedBlob = null;
let stitchedUrl = "";

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

function card(item, type) {
  const article = document.createElement("article");
  article.className = "item-card";
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
  article.append(body);
  return article;
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
        <a id="download-composition" class="tool-button download-tool">下载待发布作文图片</a>
        <p class="local-note">为保护 GitHub 仓库安全，网页不会保存上传令牌。下载后通过受保护的 GitHub 提交流程公开发布。</p>
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
  const heading = document.createElement("div");
  heading.className = "section-heading";
  heading.innerHTML = `<div><p class="kicker">${eyebrow}</p><h2>${title}</h2></div>`;
  const actions = document.createElement("div");
  actions.className = "section-actions";
  actions.innerHTML = `<span>${content[id].length} 条记录</span>`;
  if (id === "compositions") {
    const upload = document.createElement("button");
    upload.className = "upload-trigger";
    upload.textContent = "上传作文";
    upload.addEventListener("click", () => document.querySelector("#password-dialog").showModal());
    actions.append(upload);
  }
  heading.append(actions);
  section.append(heading);
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

const passwordDialog = document.querySelector("#password-dialog");
const passwordInput = document.querySelector("#upload-password");
const passwordMessage = document.querySelector("#password-message");
document.querySelector("#close-password").addEventListener("click", () => passwordDialog.close());
document.querySelector("#unlock-upload").addEventListener("click", async () => {
  const bytes = new TextEncoder().encode(passwordInput.value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hash = [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  if (hash !== UPLOAD_PASSWORD_HASH) {
    passwordMessage.textContent = "密码不正确。";
    return;
  }
  passwordMessage.textContent = "";
  passwordInput.value = "";
  passwordDialog.close();
  document.querySelector(".composition-uploader").classList.add("unlocked");
  document.querySelector(".composition-uploader").scrollIntoView({ behavior: "smooth", block: "start" });
});

const imageInput = document.querySelector("#composition-images");
const titleInput = document.querySelector("#composition-title");
const imageOrder = document.querySelector("#image-order");
const uploadMessage = document.querySelector("#upload-message");
const compositionCanvas = document.querySelector("#composition-canvas");
const previewPlaceholder = document.querySelector("#preview-placeholder");
const downloadComposition = document.querySelector("#download-composition");

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
    canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("无法生成拼接图片。")), "image/jpeg", 0.94);
  });
}

async function autoStitch() {
  if (stitchedUrl) URL.revokeObjectURL(stitchedUrl);
  stitchedBlob = null;
  stitchedUrl = "";
  downloadComposition.classList.remove("ready");
  if (compositionFiles.length < 2) {
    compositionCanvas.style.display = "none";
    previewPlaceholder.style.display = "grid";
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
    stitchedUrl = URL.createObjectURL(stitchedBlob);
    downloadComposition.href = stitchedUrl;
    downloadComposition.download = `${titleInput.value.trim() || "Claire-作文"}.jpg`;
    downloadComposition.classList.add("ready");
    previewPlaceholder.style.display = "none";
    compositionCanvas.style.display = "block";
    setUploadMessage(`自动拼接完成：共 ${images.length} 张照片，统一宽度 ${targetWidth}px。`);
  } catch (error) {
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
  downloadComposition.download = `${titleInput.value.trim() || "Claire-作文"}.jpg`;
});

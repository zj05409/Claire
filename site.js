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
  article.className = `item-card${type === "作文" ? " composition-card" : ""}`;
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

  if (type === "作文") {
    const link = document.createElement("a");
    const version = window.CLAIRE_COMPOSITIONS_VERSION || Date.now();
    link.href = `composition.html?id=${encodeURIComponent(item.slug)}&v=${encodeURIComponent(version)}`;
    link.textContent = "阅读完整作文 →";
    body.append(link);
    article.addEventListener("click", (event) => {
      if (event.target.closest("a")) return;
      location.href = link.href;
    });
    article.tabIndex = 0;
    article.addEventListener("keydown", (event) => {
      if (event.key === "Enter") location.href = link.href;
    });
  } else if (item.link) {
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

sections.forEach(({ id, title, eyebrow, empty, type }) => {
  const section = document.createElement("section");
  section.id = id;
  section.className = "collection section";
  section.innerHTML = `<div class="section-heading"><div><p class="kicker">${eyebrow}</p><h2>${title}</h2></div><span>${content[id].length} 条记录</span></div>`;
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

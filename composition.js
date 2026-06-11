const slug = new URLSearchParams(location.search).get("id");
const composition = window.CLAIRE_CONTENT.compositions.find((item) => item.slug === slug);

if (!composition) {
  document.querySelector("#detail-title").textContent = "没有找到这篇作文";
  document.querySelector("#detail-summary").textContent = "请返回作文列表重新选择。";
} else {
  document.title = `${composition.title} · Claire 的作文`;
  document.querySelector("#detail-title").textContent = composition.title;
  document.querySelector("#detail-meta").textContent = composition.date ? `发布于 ${composition.date}` : "";
  document.querySelector("#detail-summary").textContent = composition.summary || "";
  const image = document.querySelector("#full-composition-image");
  image.src = composition.image;
  image.alt = composition.title;
  document.querySelector("#full-image-link").href = composition.image;
}

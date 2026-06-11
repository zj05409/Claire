const slug = new URLSearchParams(location.search).get("id");

function findComposition() {
  return (window.CLAIRE_COMPOSITIONS || []).find((item) => item.slug === slug);
}

function renderComposition(composition) {
  if (!composition) {
    document.querySelector("#detail-title").textContent = "没有找到这篇作文";
    document.querySelector("#detail-summary").textContent = "请返回作文列表重新选择。";
    return;
  }
  document.title = `${composition.title} · Claire 的作文`;
  document.querySelector("#detail-title").textContent = composition.title;
  document.querySelector("#detail-meta").textContent = composition.date ? `发布于 ${composition.date}` : "";
  document.querySelector("#detail-summary").textContent = composition.summary || "";
  const image = document.querySelector("#full-composition-image");
  image.src = composition.image;
  image.alt = composition.title;
  document.querySelector("#full-image-link").href = composition.image;
}

async function loadLatestComposition() {
  let composition = findComposition();
  if (!composition && slug) {
    await new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = `compositions-data.js?v=${Date.now()}`;
      script.onload = resolve;
      script.onerror = resolve;
      document.head.append(script);
    });
    composition = findComposition();
  }
  renderComposition(composition);
}

loadLatestComposition();

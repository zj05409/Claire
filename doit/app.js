const screens = {
  decide: document.querySelector("#decide-screen"),
  launch: document.querySelector("#launch-screen"),
  doing: document.querySelector("#doing-screen"),
  done: document.querySelector("#done-screen"),
};

const taskInput = document.querySelector("#task");
const actionInput = document.querySelector("#first-action");
const formMessage = document.querySelector("#form-message");
const countdown = document.querySelector("#countdown");
const startedButton = document.querySelector("#started-button");
const timer = document.querySelector("#timer");
const historyList = document.querySelector("#history-list");
const emptyHistory = document.querySelector("#empty-history");

let currentTask = "";
let currentAction = "";
let startedAt = null;
let countdownInterval = null;
let timerInterval = null;

function showScreen(name) {
  Object.values(screens).forEach((screen) => screen.classList.remove("active"));
  screens[name].classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function startCountdown() {
  let remaining = 5;
  countdown.textContent = remaining;
  startedButton.classList.add("hidden");
  clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
    remaining -= 1;
    countdown.textContent = remaining > 0 ? remaining : "走";
    if (remaining <= 0) {
      clearInterval(countdownInterval);
      startedButton.classList.remove("hidden");
      startedButton.focus();
    }
  }, 1000);
}

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function startTimer() {
  startedAt = Date.now();
  timer.textContent = "00:00";
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startedAt) / 1000);
    timer.textContent = formatDuration(elapsed);
  }, 1000);
}

function getHistory() {
  try {
    return JSON.parse(localStorage.getItem("xiaocheng-action-history")) || [];
  } catch {
    return [];
  }
}

function renderHistory() {
  const history = getHistory();
  historyList.replaceChildren();
  emptyHistory.hidden = history.length > 0;

  history.slice(0, 12).forEach((item) => {
    const li = document.createElement("li");
    const title = document.createElement("strong");
    const details = document.createElement("small");
    title.textContent = item.task;
    details.textContent = `${item.status} · 第一动作：${item.action} · 行动 ${formatDuration(item.seconds)} · ${item.date}`;
    li.append(title, details);
    historyList.append(li);
  });
}

function saveResult(status) {
  clearInterval(timerInterval);
  const seconds = startedAt ? Math.max(1, Math.floor((Date.now() - startedAt) / 1000)) : 0;
  const history = getHistory();
  history.unshift({
    task: currentTask,
    action: currentAction,
    seconds,
    status,
    date: new Date().toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }),
  });
  localStorage.setItem("xiaocheng-action-history", JSON.stringify(history.slice(0, 30)));
  document.querySelector("#done-summary").textContent =
    `${status}：“${currentTask}”。你行动了 ${formatDuration(seconds)}，最重要的是你没有只停在决定上。`;
  renderHistory();
  showScreen("done");
}

document.querySelector("#decide-button").addEventListener("click", () => {
  currentTask = taskInput.value.trim();
  currentAction = actionInput.value.trim();
  if (!currentTask || !currentAction) {
    formMessage.textContent = "请先写下要做的事和最小的第一步。";
    (!currentTask ? taskInput : actionInput).focus();
    return;
  }
  formMessage.textContent = "";
  document.querySelector("#launch-task").textContent = currentTask;
  document.querySelector("#launch-action").textContent = currentAction;
  document.querySelector("#doing-task").textContent = currentTask;
  showScreen("launch");
  startCountdown();
});

startedButton.addEventListener("click", () => {
  showScreen("doing");
  startTimer();
});

document.querySelector("#finish-button").addEventListener("click", () => saveResult("完成"));
document.querySelector("#pause-button").addEventListener("click", () => saveResult("已经开始"));

document.querySelector("#new-button").addEventListener("click", () => {
  taskInput.value = "";
  actionInput.value = "";
  currentTask = "";
  currentAction = "";
  showScreen("decide");
  taskInput.focus();
});

document.querySelector("#clear-button").addEventListener("click", () => {
  if (window.confirm("确定要清空行动记录吗？")) {
    localStorage.removeItem("xiaocheng-action-history");
    renderHistory();
  }
});

[taskInput, actionInput].forEach((input) => {
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      document.querySelector("#decide-button").click();
    }
  });
});

renderHistory();
taskInput.focus();

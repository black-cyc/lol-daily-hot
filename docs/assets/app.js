const sourceNames = { bilibili: "B站", weibo: "微博", hupu: "虎扑", douyin: "抖音" };
const elements = {
  date: document.querySelector("#report-date"),
  updated: document.querySelector("#updated-at"),
  mode: document.querySelector("#cluster-mode"),
  sourceStatus: document.querySelector("#source-status"),
  sourceSummary: document.querySelector("#source-summary"),
  topicCount: document.querySelector("#topic-count"),
  topicList: document.querySelector("#topic-list"),
  notice: document.querySelector("#notice"),
  selector: document.querySelector("#history-date"),
  template: document.querySelector("#topic-template"),
};

function formatTime(value) {
  try {
    return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai" }).format(new Date(value));
  } catch (_) { return value || "--"; }
}

function compactNumber(value) {
  return new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 }).format(Number(value || 0));
}

function showNotice(message) {
  elements.notice.textContent = message;
  elements.notice.hidden = false;
}

function clearNotice() { elements.notice.hidden = true; elements.notice.textContent = ""; }

function makeEmpty(text) {
  const item = document.createElement("li");
  item.className = "empty";
  item.textContent = text;
  return item;
}

function renderSources(sources = {}) {
  elements.sourceStatus.replaceChildren();
  let healthy = 0;
  Object.entries(sourceNames).forEach(([key, name]) => {
    const source = sources[key] || { status: "failed", count: 0, error: "本次没有来源状态" };
    const item = document.createElement("div");
    item.className = `source-item ${source.status === "ok" ? "ok" : "failed"}`;
    const label = document.createElement("span");
    label.className = "source-name";
    label.textContent = name;
    const detail = document.createElement("span");
    detail.className = "source-meta";
    detail.textContent = source.status === "ok" ? `${source.count || 0} 条` : "采集失败";
    if (source.status === "ok") healthy += 1;
    if (source.error) {
      const error = document.createElement("span");
      error.className = "source-error";
      error.title = source.error;
      error.textContent = source.error;
      detail.append(error);
    }
    item.append(label, detail);
    elements.sourceStatus.append(item);
  });
  elements.sourceSummary.textContent = `${healthy}/${Object.keys(sourceNames).length} 个来源可用`;
}

function appendItem(list, item, isDouyin) {
  const li = document.createElement("li");
  const link = document.createElement("a");
  link.className = "item-link";
  link.href = item.url || "#";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = item.title || "未命名内容";
  const meta = document.createElement("div");
  meta.className = "item-meta";
  if (isDouyin) {
    const author = document.createElement("span");
    author.textContent = item.author || "抖音";
    const likes = document.createElement("span");
    likes.className = "likes";
    likes.textContent = `${compactNumber(item.like_count)} 赞`;
    meta.append(author, likes);
  } else {
    const platform = document.createElement("span");
    platform.className = "platform";
    platform.textContent = sourceNames[item.source] || item.source || "网页";
    meta.append(platform);
  }
  li.append(link, meta);
  list.append(li);
}

function renderTopics(topics = []) {
  elements.topicList.replaceChildren();
  elements.topicCount.textContent = `${topics.length} 个话题`;
  if (!topics.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "今日暂无可归并的话题。请查看上方数据源状态，下一次更新会自动重试。";
    elements.topicList.append(empty);
    return;
  }
  topics.forEach((topic, index) => {
    const node = elements.template.content.cloneNode(true);
    node.querySelector(".topic-index").textContent = String(index + 1).padStart(2, "0");
    node.querySelector("h3").textContent = topic.title;
    node.querySelector(".topic-summary").textContent = topic.summary;
    const keywords = node.querySelector(".keyword-list");
    (topic.keywords || []).forEach((word) => {
      const tag = document.createElement("span");
      tag.className = "keyword";
      tag.textContent = word;
      keywords.append(tag);
    });
    const sourceList = node.querySelector(".source-links ul");
    const douyinList = node.querySelector(".douyin-links ul");
    const content = topic.items || [];
    const videos = topic.douyin_videos || [];
    content.length ? content.slice(0, 8).forEach((item) => appendItem(sourceList, item, false)) : sourceList.append(makeEmpty("暂无相关内容"));
    videos.length ? videos.forEach((item) => appendItem(douyinList, item, true)) : douyinList.append(makeEmpty("暂无符合条件的视频"));
    elements.topicList.append(node);
  });
}

function render(data) {
  clearNotice();
  elements.date.textContent = data.date ? `${data.date} 日报` : "未知日期";
  elements.updated.textContent = `更新于 ${formatTime(data.generated_at)}`;
  elements.mode.textContent = data.meta?.cluster_mode === "llm" ? "KIMI 聚合" : "本地聚类";
  renderSources(data.sources);
  renderTopics(data.topics);
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`请求失败 (${response.status})`);
  return response.json();
}

async function loadReport(path) {
  elements.topicList.replaceChildren();
  const loading = document.createElement("p");
  loading.className = "empty";
  loading.textContent = "正在读取日报...";
  elements.topicList.append(loading);
  try { render(await fetchJson(path)); }
  catch (error) {
    renderSources({});
    elements.topicCount.textContent = "--";
    showNotice(`日报暂时无法读取：${error.message}。请稍后重试，或确认使用静态 HTTP 服务访问此页面。`);
    elements.topicList.replaceChildren();
  }
}

async function initialise() {
  try {
    const index = await fetchJson("./data/index.json");
    const dates = index.dates || [];
    elements.selector.replaceChildren();
    dates.forEach((date) => {
      const option = document.createElement("option");
      option.value = date;
      option.textContent = date;
      elements.selector.append(option);
    });
    elements.selector.disabled = !dates.length;
    elements.selector.addEventListener("change", () => loadReport(`./data/${elements.selector.value}.json`));
    await loadReport("./data/latest.json");
  } catch (error) {
    elements.selector.replaceChildren(new Option("无可用历史数据", ""));
    showNotice(`无法读取历史索引：${error.message}。请确认数据流水线已完成。`);
    renderSources({});
  }
}

initialise();

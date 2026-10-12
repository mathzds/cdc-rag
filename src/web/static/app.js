import { askStream, getJson } from "./api.js";
import { lawHtml, markdown } from "./format.js";

const OFFLINE =
  "O servidor não respondeu. Confira se o comando cdc-rag web está rodando.";
const WHEN = {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
};

const $ = (id) => document.getElementById(id);
const el = (tag, props, ...children) => {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
};

const articles = new Map();
const isArticle = (id) => articles.has(id);
const ready = getJson("/api/articles")
  .then((list) => list.forEach((a) => articles.set(a.id, a.text)))
  .catch(() => {});
let busy = false;

function addExchange(question) {
  $("empty").hidden = true;
  const x = {
    answer: el("div", { className: "answer" }),
    status: el("p", { className: "status", hidden: true }),
    sources: el("p", { className: "sources", hidden: true }),
  };
  x.root = el(
    "article",
    { className: "exchange" },
    el("p", { className: "question" }, question),
    x.answer,
    x.status,
    x.sources,
  );
  $("column").append(x.root);
  return x;
}

function setStatus(x, text) {
  x.status.textContent = text;
  x.status.hidden = !text;
}

function showSources(x, ids) {
  const buttons = ids.map((id) => {
    const b = el("button", { type: "button", className: "cite" }, id);
    b.dataset.art = id;
    return b;
  });
  x.sources.replaceChildren("Artigos consultados: ", ...buttons);
  x.sources.hidden = !ids.length;
}

function finish(x) {
  x.answer
    .querySelectorAll(".mark")
    .forEach((m, i) => m.style.setProperty("--i", i));
  requestAnimationFrame(() =>
    requestAnimationFrame(() => x.root.classList.add("done")),
  );
}

function setBusy(on) {
  busy = on;
  $("send").disabled = on;
}

function ask(question) {
  const q = question.trim();
  if (busy || !q) return false;
  answer(q);
  return true;
}

async function answer(question) {
  setBusy(true);
  await ready;
  const x = addExchange(question);
  x.root.setAttribute("aria-busy", "true");
  setStatus(x, "Procurando os artigos...");
  scrollDown();
  let text = "";
  try {
    for await (const msg of askStream(question)) {
      if (msg.sources) {
        showSources(x, msg.sources);
        setStatus(x, "Escrevendo a resposta...");
      } else {
        text += msg.chunk;
        x.answer.innerHTML = markdown(text, isArticle);
        scrollDown();
      }
    }
    finish(x);
    loadHistory();
  } catch (err) {
    x.root.append(
      el(
        "p",
        { className: "error" },
        err instanceof TypeError ? OFFLINE : err.message,
      ),
    );
  } finally {
    setStatus(x, "");
    x.root.removeAttribute("aria-busy");
    setBusy(false);
  }
}

function clearThread() {
  $("column")
    .querySelectorAll(".exchange")
    .forEach((e) => e.remove());
  $("history")
    .querySelectorAll("[aria-current]")
    .forEach((b) => b.removeAttribute("aria-current"));
}

const scrollDown = () => ($("thread").scrollTop = $("thread").scrollHeight);

function openArticle(id) {
  const text = articles.get(id);
  if (!text) return;
  $("article-num").textContent = id.replace("Art. ", "");
  $("article-text").innerHTML = lawHtml(text);
  $("article").showModal();
}

const closeMenu = () => $("sidebar").togglePopover(false);

async function loadHistory() {
  const items = await getJson("/api/history").catch(() => null);
  if (!items) return;
  $("history").replaceChildren(
    ...(items.length
      ? items.map(historyItem)
      : [el("li", { className: "none" }, "Suas perguntas aparecem aqui.")]),
  );
}

function historyItem(item) {
  const asked = new Date(item.asked_at.replace(" ", "T")).toLocaleString(
    "pt-BR",
    WHEN,
  );
  const button = el(
    "button",
    { type: "button" },
    el("span", { className: "q" }, item.question),
    el("span", { className: "when" }, asked),
  );
  button.addEventListener("click", () => showSaved(item, button));
  return el("li", {}, button);
}

function showSaved(item, button) {
  clearThread();
  const x = addExchange(item.question);
  x.root.classList.add("done");
  x.answer.innerHTML = markdown(item.answer, isArticle);
  showSources(x, item.sources.split(", ").filter(Boolean));
  button.setAttribute("aria-current", "true");
  closeMenu();
}

$("form").addEventListener("submit", (e) => {
  e.preventDefault();
  if (ask($("input").value)) $("input").value = "";
});
$("input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    $("form").requestSubmit();
  }
});
$("column").addEventListener("click", (e) => {
  const cited = e.target.closest("[data-art]");
  const suggestion = e.target.closest(".suggestions button");
  if (cited) openArticle(cited.dataset.art);
  else if (suggestion) ask(suggestion.textContent);
});
$("article").addEventListener("click", (e) => {
  const r = $("article").getBoundingClientRect();
  const outside =
    e.clientX < r.left ||
    e.clientX > r.right ||
    e.clientY < r.top ||
    e.clientY > r.bottom;
  if (e.target === $("article") && outside) $("article").close();
});
$("new").addEventListener("click", () => {
  clearThread();
  $("empty").hidden = false;
  closeMenu();
  $("input").focus();
});

await ready;
loadHistory();

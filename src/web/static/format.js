const ESCAPES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};
const NOTE = /\((?:Redação dada|Incluíd[oa]|Vide|Vigência|Revogad[oa])[^)]*\)/g;

export const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ESCAPES[c]);

function inline(line, isArticle) {
  return escapeHtml(line)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\bart(?:igo)?s?\.?\s*(\d+(?:-[A-Z])?)/gi, (match, num) => {
      const id = `Art. ${num.toUpperCase()}`;
      return isArticle(id)
        ? `<button type="button" class="mark" data-art="${id}">${match}</button>`
        : match;
    });
}

export function markdown(text, isArticle = () => false) {
  const html = [];
  let list = null;
  const closeList = () => {
    if (list) html.push(`<${list.tag}>${list.items.join("")}</${list.tag}>`);
    list = null;
  };
  for (const line of text.split("\n").map((l) => l.trim())) {
    const item = line.match(/^([-*•]|\d+[.)])\s+(.*)/);
    if (item) {
      const tag = /\d/.test(item[1]) ? "ol" : "ul";
      if (list?.tag !== tag) closeList();
      list ??= { tag, items: [] };
      list.items.push(`<li>${inline(item[2], isArticle)}</li>`);
      continue;
    }
    closeList();
    const heading = line.match(/^#{1,6}\s+(.*)/);
    if (heading)
      html.push(`<p><strong>${inline(heading[1], isArticle)}</strong></p>`);
    else if (line) html.push(`<p>${inline(line, isArticle)}</p>`);
  }
  closeList();
  return html.join("");
}

export function lawHtml(text) {
  return text
    .replace(/^Art\.\s*\d+(?:-[A-Z])?\s*[º°.]?\s*/, "")
    .split(/\s(?=§\s?\d|Parágrafo único|[IVXL]+\s?-\s|[a-z]\)\s)/)
    .map(
      (p) =>
        `<p>${escapeHtml(p).replace(NOTE, '<span class="note">$&</span>')}</p>`,
    )
    .join("");
}

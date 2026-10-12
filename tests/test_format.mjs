import assert from "node:assert/strict";
import test from "node:test";

import { lawHtml, markdown } from "../src/web/static/format.js";

const known = (id) => id === "Art. 49";

test("HTML vindo do modelo é escapado", () => {
  assert.equal(markdown('<img src=x onerror="alert(1)">'), "<p>&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</p>");
});

test("negrito, listas e citação só de artigo que existe", () => {
  assert.equal(
    markdown("**Sim**, pelo art. 49 e pelo art. 999.\n\n- um\n- dois\n1. três\n### Título", known),
    '<p><strong>Sim</strong>, pelo <button type="button" class="mark" data-art="Art. 49">art. 49</button>' +
      " e pelo art. 999.</p><ul><li>um</li><li>dois</li></ul><ol><li>três</li></ol><p><strong>Título</strong></p>",
  );
});

test("texto da lei em parágrafos, com nota de redação destacada", () => {
  assert.equal(
    lawHtml("Art. 49. Caput: I - um; II - dois. Parágrafo único. Fim (Incluído pela Lei nº 1)."),
    '<p>Caput:</p><p>I - um;</p><p>II - dois.</p><p>Parágrafo único. Fim <span class="note">(Incluído pela Lei nº 1)</span>.</p>',
  );
});

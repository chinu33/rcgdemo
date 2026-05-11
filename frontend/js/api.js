window.API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`GET ${path} ${r.status}`);
    return r.json();
  },
  ws(path) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    return new WebSocket(`${proto}://${location.host}${path}`);
  },
};

window.fmt = {
  money(n, cents = false) {
    if (n == null) return "$0";
    const opts = cents ? { minimumFractionDigits: 2, maximumFractionDigits: 2 } : { maximumFractionDigits: 0 };
    return "$" + Number(n).toLocaleString("en-US", opts);
  },
  number(n) { return Number(n).toLocaleString("en-US"); },
  pct(n) { return (n >= 0 ? "+" : "") + n.toFixed(1) + "%"; },
  pad2(n) { return String(n).padStart(2, "0"); },
};

window.markdown = function (s) {
  if (!s) return "";
  // Normalize * bullets → - and break inline bullets onto their own lines.
  // LLMs sometimes output `* Item A: text * Item B: text` without newlines.
  s = s
    .replace(/^\* /gm, "- ")
    .replace(/\n\* /g, "\n- ")
    .replace(/([.!?;])\s+\*\s+(?=[A-Z])/g, "$1\n- ")   // sentence-end then inline *
    .replace(/([.!?;,])\s+-\s+(?=[A-Z*-])/g, "$1\n- "); // sentence-end then inline -

  let html = s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bullets (handles indented/nested with spaces or tabs)
  html = html.replace(/(^|\n)((?:[ \t]*- .*(?:\n|$))+)/g, (m, pre, block) => {
    const items = block.trim().split(/\n/)
      .map(l => `<li>${l.replace(/^[ \t]*- /, "").trim()}</li>`).join("");
    return `${pre}<ul>${items}</ul>`;
  });
  // Numbered lists  (1. 2. 3.)
  html = html.replace(/(^|\n)((?:\d+\. .*(?:\n|$))+)/g, (m, pre, block) => {
    const items = block.trim().split(/\n/)
      .map(l => `<li>${l.replace(/^\d+\. /, "").trim()}</li>`).join("");
    return `${pre}<ol>${items}</ol>`;
  });
  // Paragraph wrapping for stray lines
  html = html.split(/\n{2,}/).map(p =>
    /^<(h\d|ul|ol|li|strong|p)/.test(p.trim()) ? p : `<p>${p.trim()}</p>`
  ).join("");
  return html;
};

window.Annotate = (function () {
  let active  = false;
  let drawing = false;
  let lastX = 0, lastY = 0;
  let canvas = null, ctx = null;
  let badge  = null;

  function init() {
    canvas = document.createElement("canvas");
    canvas.id = "annotate-canvas";
    document.body.appendChild(canvas);

    badge = document.createElement("div");
    badge.id = "annotate-badge";
    badge.hidden = true;
    badge.innerHTML =
      `<span class="annotate-dot"></span>ANNOTATE` +
      `&ensp;&middot;&ensp;<kbd>A</kbd>&thinsp;off&ensp;&middot;&ensp;<kbd>C</kbd>&thinsp;clear`;
    document.body.appendChild(badge);

    sizeCanvas();
    window.addEventListener("resize", sizeCanvas);

    // Mouse
    canvas.addEventListener("mousedown",  onDown);
    canvas.addEventListener("mousemove",  onMove);
    canvas.addEventListener("mouseup",    onUp);
    canvas.addEventListener("mouseleave", onUp);

    // Touch
    canvas.addEventListener("touchstart", e => { e.preventDefault(); onDown(e.touches[0]); }, { passive: false });
    canvas.addEventListener("touchmove",  e => { e.preventDefault(); onMove(e.touches[0]); }, { passive: false });
    canvas.addEventListener("touchend",   onUp);

    // Global key handler — fires on every tab
    document.addEventListener("keydown", handleKey);
  }

  // ── Canvas sizing ──────────────────────────────────────────────────────────

  function sizeCanvas() {
    if (!canvas) return;
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    applyCtx();
  }

  function applyCtx() {
    ctx = canvas.getContext("2d");
    ctx.strokeStyle = "#00ff88";
    ctx.lineWidth   = 4;
    ctx.lineCap     = "round";
    ctx.lineJoin    = "round";
    ctx.shadowBlur  = 0;
  }

  // ── Drawing ────────────────────────────────────────────────────────────────

  function onDown(e) {
    drawing = true;
    [lastX, lastY] = [e.clientX, e.clientY];
  }

  function onMove(e) {
    if (!drawing) return;
    const x = e.clientX, y = e.clientY;
    ctx.beginPath();
    ctx.moveTo(lastX, lastY);
    ctx.lineTo(x, y);
    ctx.stroke();
    [lastX, lastY] = [x, y];
  }

  function onUp() { drawing = false; }

  // ── Public API ─────────────────────────────────────────────────────────────

  function toggle() {
    active ? disable() : enable();
  }

  function enable() {
    active = true;
    canvas.style.pointerEvents = "all";
    badge.hidden = false;
    document.body.classList.add("annotating");
  }

  function disable() {
    active  = false;
    drawing = false;
    canvas.style.pointerEvents = "none";
    badge.hidden = true;
    document.body.classList.remove("annotating");
  }

  function clear() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    applyCtx(); // clearRect preserves ctx settings, but applyCtx is cheap insurance
  }

  function isActive() { return active; }

  // ── Key handler ────────────────────────────────────────────────────────────

  function handleKey(e) {
    // Never fire when the user is typing
    if (e.target.matches("input, textarea, select, [contenteditable]")) return;
    if (e.key === "a" || e.key === "A") {
      e.preventDefault();
      toggle();
    } else if ((e.key === "c" || e.key === "C") && active) {
      e.preventDefault();
      clear();
    }
  }

  document.addEventListener("DOMContentLoaded", init);

  return { toggle, enable, disable, clear, isActive };
})();

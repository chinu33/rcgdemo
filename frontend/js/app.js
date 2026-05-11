window.App = (function () {
  const MIN_SPLASH_MS = 900;
  const splash = () => document.getElementById("splash");
  const splashStatus = () => document.getElementById("splash-status");

  function setSplash(text) {
    const el = splashStatus();
    if (el) el.textContent = text;
  }

  function dismissSplash() {
    const s = splash();
    if (!s) return;
    s.classList.add("hidden");
    document.body.classList.remove("app-booting");
    setTimeout(() => { if (s.parentNode) s.parentNode.removeChild(s); }, 700);
  }

  let lastTab = "dashboard";

  function switchTab(name) {
    document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === `panel-${name}`));
    const content = document.querySelector(".content");
    if (content) content.scrollTop = 0;
    if (lastTab === "pitch" && name !== "pitch" && window.Pitch) Pitch.deactivate();
    if (name === "pitch" && window.Pitch) Pitch.activate();
    if (name === "analytics") Analytics.load();
    if (name === "mcp") MCP.load();
    if (name === "store-manager" || name === "war-room") {
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    }
    lastTab = name;
  }

  async function bootstrap() {
    const t0 = performance.now();

    // Wire navigation early so the page is interactive even if a fetch fails
    document.querySelectorAll(".tab").forEach(t => {
      t.addEventListener("click", () => switchTab(t.dataset.tab));
    });
    document.querySelectorAll("[data-goto]").forEach(b => {
      b.addEventListener("click", () => switchTab(b.dataset.goto));
    });

    setSplash("Connecting to data layer…");
    try {
      const s = await API.get("/api/status");
      const lbl = document.getElementById("model-label");
      const dbBit = s.db ? ` · SQLite ${s.db.tables}t/${s.db.rows.toLocaleString()}r` : "";
      lbl.textContent = (s.demo_mode
        ? `Demo · ${s.model}`
        : `${s.model}${s.langsmith_enabled ? " · LangSmith" : ""}`) + dbBit;
    } catch (e) {
      const lbl = document.getElementById("model-label");
      if (lbl) lbl.textContent = "Offline";
    }

    setSplash("Loading store snapshot…");
    try {
      await Dashboard.load();
    } catch (e) {
      console.error("Dashboard load failed:", e);
      setSplash("Couldn't reach the API. Showing offline view.");
    }

    setSplash("Initializing agent network…");
    try {
      StoreManager.init();
      await WarRoom.init();
      await MCP.load();
      if (window.Pitch) Pitch.init();
    } catch (e) {
      console.error("Agent init failed:", e);
    }

    // Honor minimum splash time so the entrance feels intentional
    const elapsed = performance.now() - t0;
    const wait = Math.max(0, MIN_SPLASH_MS - elapsed);
    setSplash("Ready.");
    setTimeout(dismissSplash, wait);
  }

  // Safety net: never let the splash hang indefinitely
  setTimeout(() => {
    if (document.body.classList.contains("app-booting")) dismissSplash();
  }, 8000);

  document.addEventListener("DOMContentLoaded", bootstrap);

  return { switchTab, dismissSplash };
})();

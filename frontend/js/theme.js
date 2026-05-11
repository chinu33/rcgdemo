(function () {
  const KEY = "rcg-theme";
  const root = document.documentElement;
  const saved = localStorage.getItem(KEY);
  if (saved) root.setAttribute("data-theme", saved);

  const btn = document.getElementById("theme-toggle");
  const dark = document.getElementById("theme-icon-dark");
  const light = document.getElementById("theme-icon-light");

  function sync() {
    const isLight = root.getAttribute("data-theme") === "light";
    dark.style.display = isLight ? "none" : "";
    light.style.display = isLight ? "" : "none";
  }
  sync();

  btn?.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    root.setAttribute("data-theme", next);
    localStorage.setItem(KEY, next);
    sync();
    window.dispatchEvent(new CustomEvent("theme-changed", { detail: next }));
  });
})();

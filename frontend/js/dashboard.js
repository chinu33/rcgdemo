window.Dashboard = (function () {
  let snapshot = null;

  async function load() {
    snapshot = await API.get("/api/dashboard");
    try {
      render();
    } catch (e) {
      console.error("Dashboard render error:", e);
    }
  }

  function render() {
    if (!snapshot) return;
    const { store, today, hourly, categories, top_up, top_down, inventory_categories,
            critical_skus, labor, departments, alerts, recent_reviews, reviews_summary } = snapshot;

    document.getElementById("store-name").textContent = `${store.name} · ${store.city}`;
    const now = new Date();
    document.getElementById("hero-date").textContent = now.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
    document.getElementById("hero-greeting").textContent = `Good morning, ${store.manager.split(" ")[0]}.`;
    document.getElementById("hero-alert-count").textContent = alerts.length;

    document.getElementById("kpi-revenue").textContent = fmt.money(today.revenue_to_date);
    document.getElementById("kpi-revenue-sub").textContent = `vs ${fmt.money(today.forecast_to_date)} forecast`;

    const v = document.getElementById("kpi-variance");
    v.textContent = fmt.pct(today.variance_pct);
    v.parentElement.querySelector(".kpi-sub").className = "kpi-sub " + (today.variance_pct >= 0 ? "up" : "down");

    document.getElementById("kpi-traffic").textContent = fmt.number(today.traffic);
    document.getElementById("kpi-traffic-sub").textContent = `${today.conversion_pct}% conversion`;
    document.getElementById("kpi-basket").textContent = fmt.money(today.avg_basket, true);
    document.getElementById("kpi-tx").textContent = fmt.number(today.transactions);

    const stockoutCount = critical_skus.filter(s => s.on_hand === 0).length;
    document.getElementById("kpi-stockouts").textContent = stockoutCount;

    document.getElementById("kpi-labor").textContent = labor.labor_cost_pct_of_sales + "%";
    document.getElementById("kpi-labor-sub").textContent = `target ${labor.target_pct}%`;

    Charts.hourly("chart-hourly", hourly);
    Charts.category("chart-category", categories);

    // Alerts
    const alertsEl = document.getElementById("alerts-list");
    document.getElementById("alerts-count").textContent = alerts.length;
    alertsEl.innerHTML = alerts.map(a => `
      <div class="alert ${a.level}">
        <div class="alert-title">${a.title}</div>
        <div class="alert-detail">${a.detail}</div>
      </div>`).join("") || `<div class="alert-detail">All systems nominal.</div>`;

    // Inventory grid
    const invEl = document.getElementById("inventory-grid");
    invEl.innerHTML = inventory_categories.map(c => `
      <div class="inv-row">
        <div class="inv-name">${c.category}</div>
        <div class="inv-meta">
          <span>${c.days_of_supply.toFixed(1)}d</span>
          <span class="inv-pill ${c.alert}">${c.alert}</span>
        </div>
      </div>`).join("");

    // Reviews
    const stars = n => "★".repeat(n) + "☆".repeat(5 - n);
    document.getElementById("reviews-list").innerHTML = recent_reviews.map(r => `
      <div class="review">
        <div class="review-head">
          <span><strong>${r.author}</strong> · ${new Date(r.time).toLocaleString("en-US",{ hour:"numeric", minute:"2-digit", weekday:"short" })}</span>
          <span class="review-stars">${stars(r.rating)}</span>
        </div>
        <div class="review-text">${r.text}</div>
      </div>`).join("");
  }

  return { load, snapshot: () => snapshot };
})();

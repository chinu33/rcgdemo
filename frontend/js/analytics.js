window.Analytics = (function () {
  let loaded = false;
  let data = null;

  async function load() {
    if (loaded) return;
    data = await API.get("/api/analytics");
    Charts.revenue90("chart-rev-90", data.daily_revenue_90d, data.daily_revenue_dates);
    Charts.categoryTrend("chart-cat-30", data.categories_30d, data.category_dates);
    Charts.agentRuns("chart-agent-30", data.agent_runs_30d);
    Charts.agentBreakdown("chart-agent-bd", data.agent_breakdown);

    document.getElementById("disruption-list").innerHTML = data.disruptions_handled_90d.map(d => `
      <div class="dis-row">
        <div>
          <div><strong>${d.title}</strong></div>
          <div class="dis-meta">${d.date} · ${d.type} · ${d.stores_affected} stores</div>
        </div>
        <div><span class="badge green">${d.minutes_to_response}m response</span></div>
      </div>`).join("");

    renderDbStrip(data.db);
    loaded = true;
  }

  function renderDbStrip(stats) {
    if (!stats) return;
    document.getElementById("db-tables").textContent = stats.tables.toLocaleString();
    document.getElementById("db-rows").textContent = stats.rows.toLocaleString();
    document.getElementById("db-path").textContent = stats.path;
    const list = document.getElementById("db-tables-list");
    const entries = Object.entries(stats.by_table || {}).sort((a, b) => b[1] - a[1]);
    list.innerHTML = entries.map(([t, n]) =>
      `<span class="db-pill">${t}<span class="n">${n}</span></span>`
    ).join("");
  }

  function renderHeatmap(breakdown) {
    const el = document.getElementById("agent-heatmap");
    const maxCalls = Math.max(...breakdown.map(b => b.calls));
    const cols = 10;
    el.innerHTML = breakdown.map(b => {
      const cells = Array.from({ length: cols }, (_, i) => {
        const seed = (b.calls / maxCalls) * (0.6 + 0.4 * Math.sin((i + b.agent.length) * 0.7));
        const intensity = Math.max(0.05, Math.min(1, seed));
        const color = `rgba(124, 92, 255, ${intensity})`;
        return `<div class="hm-cell" style="background:${color}" data-tip="${b.agent} · day ${i + 1}: ~${Math.round(intensity * b.calls / cols * 30)} calls"></div>`;
      }).join("");
      return `
        <div class="hm-row">
          <div class="hm-label">${b.agent}</div>
          ${cells}
        </div>`;
    }).join("");
  }

  return { load };
})();

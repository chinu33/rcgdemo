(function () {
  // Centralised Chart.js theming + helpers
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function gradient(ctx, w, h, from, to) {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, from);
    g.addColorStop(1, to);
    return g;
  }

  function applyDefaults() {
    Chart.defaults.color = cssVar("--chart-text");
    Chart.defaults.borderColor = cssVar("--chart-grid");
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.boxHeight = 10;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
  }
  applyDefaults();
  window.addEventListener("theme-changed", () => {
    applyDefaults();
    Object.values(window._charts || {}).forEach(c => c.update());
  });

  window._charts = {};

  window.Charts = {
    hourly(canvasId, hourly) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const { width, height } = ctx.canvas;
      const labels = hourly.map(h => h.hour);
      const actual = hourly.map(h => h.revenue || null);
      const forecast = hourly.map(h => h.forecast);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      window._charts[canvasId] = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [
            {
              label: "Forecast",
              data: forecast,
              borderColor: "rgba(120,132,176,0.6)",
              borderDash: [4, 4],
              pointRadius: 0,
              tension: 0.35,
              fill: false,
            },
            {
              label: "Actual",
              data: actual,
              borderColor: cssVar("--accent-1"),
              backgroundColor: gradient(ctx, width, height, "rgba(124,92,255,0.32)", "rgba(124,92,255,0)"),
              pointBackgroundColor: cssVar("--accent-2"),
              pointRadius: 3,
              fill: true,
              tension: 0.35,
              spanGaps: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: "index" },
          plugins: {
            legend: { position: "bottom" },
            tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: $${(ctx.parsed.y || 0).toLocaleString()}` } },
          },
          scales: {
            y: { ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }, grid: { color: cssVar("--chart-grid") } },
            x: { grid: { display: false } },
          },
        },
      });
    },

    category(canvasId, categories) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const labels = categories.map(c => c.category);
      const data = categories.map(c => c.variance_pct);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      const colors = data.map(v =>
        v > 5 ? cssVar("--accent-good")
        : v < -10 ? cssVar("--accent-bad")
        : v < 0 ? cssVar("--accent-warm")
        : cssVar("--accent-2")
      );
      window._charts[canvasId] = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: "Variance %", data, backgroundColor: colors, borderRadius: 6 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { callback: v => v + "%" }, grid: { color: cssVar("--chart-grid") } },
            y: { grid: { display: false } },
          },
        },
      });
    },

    revenue90(canvasId, days, dates) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const { width, height } = ctx.canvas;
      const labels = (dates && dates.length === days.length)
        ? dates.map(d => d.slice(5))
        : days.map((_, i) => `D-${days.length - 1 - i}`);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      window._charts[canvasId] = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [{
            label: "Daily Revenue",
            data: days,
            borderColor: cssVar("--accent-2"),
            backgroundColor: gradient(ctx, width, height, "rgba(34,211,238,0.32)", "rgba(34,211,238,0)"),
            fill: true,
            tension: 0.35,
            pointRadius: 0,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => "$" + c.parsed.y.toLocaleString() } } },
          scales: {
            x: { grid: { display: false }, ticks: { maxTicksLimit: 12 } },
            y: { ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }, grid: { color: cssVar("--chart-grid") } },
          },
        },
      });
    },

    categoryTrend(canvasId, cats, dates) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const palette = [cssVar("--accent-1"), cssVar("--accent-2"), cssVar("--accent-3"), cssVar("--accent-good"), cssVar("--accent-warm"), "#a584ff", "#ff8ad4", "#f59e0b", "#34d399", "#22d3ee"];
      const datasets = Object.entries(cats).map(([name, arr], i) => ({
        label: name,
        data: arr,
        borderColor: palette[i % palette.length],
        backgroundColor: "transparent",
        tension: 0.35,
        pointRadius: 0,
        borderWidth: 2,
      }));
      const len = datasets[0]?.data.length || 0;
      const labels = (dates && dates.length === len)
        ? dates.map(d => d.slice(5))
        : Array.from({length: len}, (_, i) => `D-${len - 1 - i}`);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      window._charts[canvasId] = new Chart(ctx, {
        type: "line", data: { labels, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: "bottom" } },
          scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }, y: { ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }, grid: { color: cssVar("--chart-grid") } } },
        },
      });
    },

    agentRuns(canvasId, runs) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const { width, height } = ctx.canvas;
      const labels = runs.map(r => `D${r.day}`);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      window._charts[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            {
              label: "Runs",
              data: runs.map(r => r.runs),
              backgroundColor: gradient(ctx, width, height, "rgba(124,92,255,0.85)", "rgba(124,92,255,0.15)"),
              borderRadius: 4,
              yAxisID: "y",
            },
            {
              label: "Avg Latency (ms)",
              data: runs.map(r => r.avg_latency_ms),
              type: "line",
              borderColor: cssVar("--accent-warm"),
              backgroundColor: "transparent",
              tension: 0.4,
              pointRadius: 0,
              borderWidth: 2,
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: "bottom" } },
          scales: {
            y: { position: "left", grid: { color: cssVar("--chart-grid") } },
            y1: { position: "right", grid: { display: false }, ticks: { callback: v => v + "ms" } },
            x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
          },
        },
      });
    },

    agentBreakdown(canvasId, breakdown) {
      const ctx = document.getElementById(canvasId).getContext("2d");
      const labels = breakdown.map(b => b.agent);
      if (window._charts[canvasId]) window._charts[canvasId].destroy();
      window._charts[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "Cost ($)", data: breakdown.map(b => b.cost_usd), backgroundColor: cssVar("--accent-1"), borderRadius: 4, yAxisID: "y" },
            { label: "Avg Latency (ms)", data: breakdown.map(b => b.avg_ms), backgroundColor: cssVar("--accent-2"), borderRadius: 4, yAxisID: "y1" },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { position: "bottom" } },
          scales: {
            y: { position: "left", grid: { color: cssVar("--chart-grid") }, ticks: { callback: v => "$" + v } },
            y1: { position: "right", grid: { display: false }, ticks: { callback: v => v + "ms" } },
            x: { grid: { display: false }, ticks: { maxRotation: 45, minRotation: 45 } },
          },
        },
      });
    },
  };
})();

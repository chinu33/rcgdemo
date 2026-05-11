"""Scripted high-quality fallback responses for offline demo mode."""

STORE_MANAGER = {
    "sales": (
        "- Revenue $184.3K vs forecast $201.5K — running **-8.5%** through 11am, the worst variance in 14 days.\n"
        "- **Dairy -31.9%** and **Electronics -21.0%** are doing all the damage; Beverages (+7.8%) and Snacks (+6.1%) are bright spots.\n"
        "- Hourly pacing was on-track until ~10am, then conversion fell off — suggests a stockout or staffing issue mid-morning, not a traffic problem.\n"
        "- Avg basket holding at $65.50 (yesterday $66.47), so customers who buy are still buying — we're losing transactions, not basket size."
    ),
    "inventory": (
        "- **3 critical dairy SKUs at zero on-hand**: Chobani 32oz, Fairlife 52oz, Horizon Organic — combined lost sales est. **$3,500** today.\n"
        "- Dairy days-of-supply collapsed to **1.4** (target 3.5+); next delivery 2026-05-07, gap is severe.\n"
        "- Driscoll's strawberries (PRO-5012) only 12 units against 340/wk velocity — will be out by 2pm.\n"
        "- Frozen, Household, Personal Care all healthy (6+ days). Risk is concentrated in perishables."
    ),
    "labor": (
        "- **Dairy & Frozen department -6 hours** uncovered (3 callouts, no backfill) — directly correlates with replenishment lag.\n"
        "- Stocking overnight short by 6 hours; explains why morning shelves weren't fully reset.\n"
        "- Labor cost running 9.8% of sales vs 8.5% target — overtime triggered by callouts.\n"
        "- Recommendation: pull 4 hrs from Apparel (fully staffed, sales soft) to cover Dairy floor recovery."
    ),
    "promo": (
        "- **Mother's Day Floral promo +42% lift** — outperforming, drives 1,840 redemptions; expand endcap exposure.\n"
        "- **Apparel Spring Clearance -4.2%** lift — losing to Target's BOGO 50% across the street; consider matching tomorrow.\n"
        "- **Kroger Streeterville (1.2 mi) launched 30% off Chobani 6 days ago** — likely accelerated our dairy stockouts as customers stocked up there too.\n"
        "- Beverages B2G1 on target; no action needed."
    ),
    "reviews": (
        "- Today's rating **3.6 vs 30-day 4.2** — sentiment score -0.18 (negative).\n"
        "- **\"Empty dairy shelves\" mentions up 1,100%** vs trailing 30d — 23 mentions today alone.\n"
        "- **\"Long checkout lines\" up 220%** — likely tied to Front End coverage gap.\n"
        "- Positive theme: floral display (+340% mentions) — Mother's Day execution is landing."
    ),
    "synthesis": (
        "## Headline\n"
        "Dairy stockouts triggered by competitor promo + supplier lag are dragging today's revenue 8.5% below forecast and customer sentiment to a 30-day low.\n\n"
        "## Root cause\n"
        "Kroger Streeterville's 30% Chobani promo (started Apr 30) pulled traffic, accelerating our dairy velocity. Three Dairy & Frozen callouts left 6 hrs uncovered overnight, so replenishment from receiving never made it to the floor. By 8am, three top-velocity SKUs hit zero. Customer reviews picked it up immediately (+1,100% on \"empty dairy\" mentions), and we're losing transactions, not basket size — the lost demand is walking out the door.\n\n"
        "## Recommended actions\n"
        "- **Pull 4 hrs from Apparel to Dairy & Frozen for shelf recovery** — Owner: AsstMgr Diaz — ETA: by 1pm\n"
        "- **Emergency PO to Organic Valley Co-op (alt supplier, 3-day lead)** — Owner: Receiving Mgr Patel — ETA: today 4pm\n"
        "- **Match Kroger 30% on remaining Chobani SKUs once replenished** — Owner: Store Mgr — ETA: tomorrow open"
    ),
}

DISRUPTION = {
    "detector": (
        "- **Hurricane Ingrid, Cat 3** — landfall projected near Tampa Bay in **~48 hours** (2026-05-08).\n"
        "- Affected geography: FL, GA, SC coastal zones. Mandatory evacuations in 4 counties.\n"
        "- Blast radius: **3 RCG stores directly exposed** (ST-031 Tampa, ST-027 Atlanta, ST-061 Charlotte) plus regional DC-7."
    ),
    "supplier": (
        "- **Driscoll's Direct (SUP-PROD-11)** — Florida produce hub at risk; activate backup from Georgia line.\n"
        "- **Coca-Cola Bottling Midwest (SUP-BEV-44)** — solid; pre-position bottled water surge orders now.\n"
        "- Recommended sourcing pivot: shift 60% of perishable orders for ST-031 to Atlanta DC, accept 1-day lead penalty.\n"
        "- No exposure on Apex Electronics — already routed via inland."
    ),
    "rebalancer": (
        "- Pre-position **48 pallets of bottled water + batteries** to ST-031 and ST-027 from DC-7 within 24h.\n"
        "- Move generators (8 units) and plywood (200 sheets) from ST-058 Plano (over-stocked) to ST-031 Tampa.\n"
        "- Hold ST-061 Charlotte at current levels — likely to absorb evacuee demand inland.\n"
        "- Risk: over-positioning perishables to ST-031 if landfall shifts; cap dairy/produce at 1.5x normal."
    ),
    "impact": (
        "- **ST-031 Tampa** highest exposure: $1.4M revenue at risk over 7 days (closure + post-storm cleanup).\n"
        "- **ST-027 Atlanta** $480K at risk — likely reduced traffic, no closure.\n"
        "- **ST-061 Charlotte** could see +$220K surge demand from evacuees if positioned correctly.\n"
        "- Net network impact: **-$1.66M** baseline, **-$1.20M** with proactive rebalancing."
    ),
    "comms": (
        "=== SUPPLIER_EMAIL ===\n"
        "Subject: Hurricane Ingrid contingency — request status + alternate fulfillment\n\n"
        "Team,\n\n"
        "Hurricane Ingrid is projected to make landfall near Tampa in ~48 hours. We need by EOD today: (1) status of in-transit orders to ST-031, ST-027, ST-061; (2) confirmation of alternate fulfillment from your Atlanta line for the next 7 days; (3) any force majeure declarations you anticipate.\n\n"
        "We are pre-positioning surge categories now and would like to coordinate.\n\n"
        "Thanks,\n"
        "RCG Supply Resilience\n\n"
        "=== CUSTOMER_NOTICE ===\n"
        "We're monitoring Hurricane Ingrid closely and pre-positioning essentials at our Florida and Georgia stores. Some items may sell out faster than usual — check store availability before visiting."
    ),
    "synthesis": (
        "## Situation\n"
        "Hurricane Ingrid (Cat 3) makes landfall near Tampa in ~48 hours; 3 stores directly exposed with **$1.66M** revenue at risk over 7 days, reducible to **$1.20M** with proactive action.\n\n"
        "## Decisions needed in next 60 minutes\n"
        "- **Approve $480K emergency surge PO** (water, batteries, generators) — Owner: VP Supply Chain\n"
        "- **Authorize ST-031 closure protocol trigger at T-12h** — Owner: Regional Director South\n"
        "- **Greenlight Atlanta-line failover for produce/dairy** — Owner: Merchandising Lead\n\n"
        "## Auto-actions taken\n"
        "- Drafted supplier escalation email (Driscoll's, Coca-Cola, Prairie Farms) — pending one-click send.\n"
        "- Generated customer-facing notice for FL/GA store pages — staged for approval.\n"
        "- Built inter-store transfer plan (DC-7 → ST-031, ST-027; ST-058 → ST-031) — ready to dispatch."
    ),
}

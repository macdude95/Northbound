#!/usr/bin/env python3
"""
Weekly TQQQ Hedged-DCA action card.

A standalone, simplified take on a leveraged-ETF accumulation strategy: a
throttled weekly DCA into TQQQ plus an exposure-ramped protective-put hedge.
It fetches QQQ + TQQQ from the Yahoo Finance chart API, reads your current
position from a local state file, and prints an action card telling you how
much to buy and whether to touch the hedge.

Self-contained: pure Python standard library (3.7+). No third-party packages,
no API key, and nothing from this repo's requirements.txt is needed.

READ-ONLY: this script never places a trade and never writes any file. It only
reads tqqq-state.json and prints a recommendation.

State file:
  Looked up at $TQQQ_VAULT/tqqq-state.json, defaulting to ~/Nexus/tqqq-state.json.
  The state file holds your real position and is intentionally NOT committed to
  this repo (see .gitignore). Keep it outside version control.
"""
import calendar
import json
import math
import os
import urllib.request
from datetime import date, datetime

# State lives outside the repo (it contains your real holdings). Default to the
# Obsidian vault; override with the TQQQ_VAULT env var on other machines.
VAULT = os.path.expanduser(os.environ.get("TQQQ_VAULT", "~/Nexus"))
STATE_PATH = os.path.join(VAULT, "tqqq-state.json")

# ===== CONFIG =====
CONFIG = {
    "base_weekly_usd": 500,        # base weekly DCA dollar amount
    "mode": "throttled",           # "throttled" (SMA tiers below) or "flat" (always 1x)

    # --- Hedge: exposure-ramped (coverage grows as TQQQ grows vs the reserve) ---
    "hedge_mode": "ramped",            # "ramped" or "fixed"
    "hedge_max_coverage_pct": 0.50,    # coverage cap once fully ramped
    "hedge_ramp_start_ratio": 0.50,    # TQQQ/reserve below this -> 0% hedge (cash is the buffer)
    "hedge_ramp_full_ratio": 1.00,     # TQQQ/reserve at/above this -> full max coverage
    "hedge_coverage_pct": 0.50,        # used only when hedge_mode == "fixed"

    # --- Put mechanics (only matter once the hedge is actually on) ---
    "hedge_otm_pct": 0.20,         # suggested put strike = TQQQ price * (1 - this)
    "hedge_tenor_months": 12,      # target expiry horizon when buying / rolling puts
    "roll_dte_threshold": 90,      # roll the put when days-to-expiry drops below this
}
# Throttle tiers as (lower_bound_pct, multiplier); pct = (QQQ - 200dSMA) / 200dSMA * 100
TIERS = [(10, 0.5), (0, 1.0), (-10, 1.5), (-20, 2.0), (-(10 ** 9), 3.0)]
# ==================

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}


def fetch(symbol, rng="1y"):
    """Return (current_price, [daily_closes]) from Yahoo Finance chart API."""
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
           "?range=%s&interval=1d" % (symbol, rng))
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    res = data["chart"]["result"][0]
    price = float(res["meta"]["regularMarketPrice"])
    closes = [float(c) for c in res["indicators"]["quote"][0]["close"] if c is not None]
    return price, closes


def multiplier_for(pct):
    if CONFIG["mode"] == "flat":
        return 1.0
    for bound, mult in TIERS:
        if pct >= bound:
            return mult
    return TIERS[-1][1]


def tier_label(pct):
    if pct >= 10:
        return "Extended"
    if pct >= 0:
        return "Normal"
    if pct >= -10:
        return "Dip"
    if pct >= -20:
        return "Deep dip"
    return "Crash"


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"tqqq_shares": 0, "reserve_usd": 0, "puts": []}


def hedge_target_pct(tqqq_notional, reserve):
    """Return (coverage_fraction, exposure_ratio).

    Exposure-ramped: while TQQQ is small relative to the cash reserve, the
    reserve itself is the buffer and we hold no puts. As TQQQ grows toward and
    past the reserve, coverage ramps linearly from 0 up to the cap.
    """
    if CONFIG["hedge_mode"] == "fixed":
        ratio = (tqqq_notional / reserve) if reserve > 0 else 0.0
        return CONFIG["hedge_coverage_pct"], ratio
    if reserve <= 0:
        ratio = float("inf") if tqqq_notional > 0 else 0.0
    else:
        ratio = tqqq_notional / reserve
    start = CONFIG["hedge_ramp_start_ratio"]
    full = CONFIG["hedge_ramp_full_ratio"]
    cap = CONFIG["hedge_max_coverage_pct"]
    if ratio <= start:
        frac = 0.0
    elif ratio >= full:
        frac = 1.0
    else:
        frac = (ratio - start) / (full - start)
    return cap * frac, ratio


def suggest_expiry(today):
    tm = today.month - 1 + CONFIG["hedge_tenor_months"]
    year = today.year + tm // 12
    month = tm % 12 + 1
    return "%s %d" % (calendar.month_abbr[month], year)


def main():
    state = load_state()
    qqq_price, qqq_closes = fetch("QQQ")
    tqqq_price, _ = fetch("TQQQ")

    window = qqq_closes[-200:]
    sma200 = sum(window) / len(window)
    pct = (qqq_price - sma200) / sma200 * 100.0
    mult = multiplier_for(pct)
    weekly_usd = CONFIG["base_weekly_usd"] * mult
    shares = int(weekly_usd // tqqq_price)
    spend = shares * tqqq_price

    shares_held = state.get("tqqq_shares", 0)
    reserve = state.get("reserve_usd", 0)
    tqqq_notional = shares_held * tqqq_price
    coverage, ratio = hedge_target_pct(tqqq_notional, reserve)
    target_contracts = math.ceil(shares_held * coverage / 100.0)
    puts = state.get("puts", [])
    have_contracts = sum(p.get("contracts", 0) for p in puts)

    today = date.today()
    min_dte = None
    for p in puts:
        try:
            d = (datetime.strptime(p["expiry"], "%Y-%m-%d").date() - today).days
            min_dte = d if min_dte is None else min(min_dte, d)
        except Exception:
            pass

    strike = round(tqqq_price * (1 - CONFIG["hedge_otm_pct"]))
    exp = suggest_expiry(today)

    print("=== TQQQ Action Card  %s ===" % today.isoformat())
    print("QQQ $%.2f | 200d SMA $%.2f | %+.1f%% vs SMA  ->  Tier: %s (%.1fx)"
          % (qqq_price, sma200, pct, tier_label(pct), mult))
    print("TQQQ $%.2f" % tqqq_price)
    print("")
    print("1) DCA  : Buy $%.0f of TQQQ  ~=  %d shares @ $%.2f  (= $%.0f)"
          % (weekly_usd, shares, tqqq_price, spend))

    if shares_held == 0:
        print("2) HEDGE: No position yet -> initiate when ready; no hedge needed.")
    else:
        print("   Exposure: TQQQ $%.0f vs reserve $%.0f  =  %.0f%% of reserve "
              "(hedge: 0%% below 50%%, ramps to 50%% cover by 100%%)"
              % (tqqq_notional, reserve, ratio * 100.0))
        if coverage <= 0:
            print("2) HEDGE: UNHEDGED, and that is fine - TQQQ is below 50%% of your reserve.")
            print("         ->  No put needed yet. The card will flag you when to start.")
        else:
            print("2) HEDGE: target %.0f%% coverage = %d put(s); you hold %d | nearest DTE %s"
                  % (coverage * 100, target_contracts, have_contracts,
                     "n/a" if min_dte is None else str(min_dte)))
            actions = []
            if have_contracts < target_contracts:
                actions.append("BUY %d put(s) ~$%d strike, exp ~%s"
                               % (target_contracts - have_contracts, strike, exp))
            if min_dte is not None and min_dte < CONFIG["roll_dte_threshold"]:
                actions.append("ROLL nearest put out to ~%s (strike ~$%d)" % (exp, strike))
            print("         ->  %s" % ("; ".join(actions) if actions else "HOLD (no action)"))

    print("")
    print("Reserve after buy: $%.0f" % (reserve - spend))
    print("(Recommendation only. Place trades yourself, then reply with what you did.)")


if __name__ == "__main__":
    main()

"""FX oracle — fully on-chain, via Pyth price feeds on Arc.

Three real Pyth feeds (read-only `getPriceUnsafe`, no fees):
  - EUR/USD  (FX)     -> the true value of a euro in USD
  - EURC/USD (crypto) -> what the EURC stablecoin actually trades at
  - USDC/USD (crypto) -> what USDC actually trades at

The basis is EURC's deviation from its own EUR peg:
    basis = EURC/USD  /  EUR/USD  - 1
A negative basis means EURC trades *below* the euro it's pegged to, so buying
EURC delivers euro-value at a discount — the dislocation the agent captures.

Every read carries a confidence interval and publish time, so the agent gates on
freshness + tightness before acting on a price (see FxQuote.usable).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pyth


@dataclass
class FxQuote:
    real_usd_per_eur: float | None      # Pyth EUR/USD (FX) — true euro value
    onchain_usd_per_eur: float | None   # Pyth EURC/USD — what EURC trades at
    usdc_usd: float | None              # Pyth USDC/USD
    basis_pct: float | None             # EURC/USD / EUR/USD - 1 (EURC peg deviation)
    onchain_source: str                 # "pyth"
    oldest_age_s: float | None          # freshness of the stalest feed
    widest_conf_bps: float | None       # uncertainty of the widest feed
    usable: bool                        # fresh + tight enough to act on


@dataclass
class Route:
    path: Literal["onchain_swap", "direct_usdc"]
    rationale: str
    est_savings_bps: float


def get_quote() -> FxQuote:
    """Read EUR/USD, EURC/USD, USDC/USD from Pyth on Arc and compute the basis."""
    eur = pyth.eur_usd()
    eurc = pyth.eurc_usd()
    usdc = pyth.usdc_usd()
    basis = (eurc.price / eur.price - 1) if (eur.price and eurc.price) else None
    return FxQuote(
        real_usd_per_eur=eur.price,
        onchain_usd_per_eur=eurc.price,
        usdc_usd=usdc.price,
        basis_pct=basis,
        onchain_source="pyth",
        oldest_age_s=max(eur.age_seconds, eurc.age_seconds, usdc.age_seconds),
        widest_conf_bps=max(eur.rel_conf_bps, eurc.rel_conf_bps, usdc.rel_conf_bps),
        usable=eur.is_usable() and eurc.is_usable() and usdc.is_usable(),
    )


def decide_route(quote: FxQuote, send_ccy: str, recv_ccy: str) -> Route:
    """Pick the cheapest settlement path, gating on oracle quality first."""
    if not quote.usable:
        return Route("direct_usdc",
                     "Oracle price stale or uncertain — settle safely in USDC, no FX bet",
                     0.0)
    if recv_ccy == "EUR" and quote.basis_pct is not None and quote.basis_pct < 0:
        return Route("onchain_swap",
                     "EURC trades below its EUR peg on Arc (Pyth) — buy EURC to capture the discount",
                     round(abs(quote.basis_pct) * 1e4, 1))
    return Route("direct_usdc",
                 "No favorable EURC dislocation — settle directly in USDC",
                 0.0)


if __name__ == "__main__":
    import json
    from dataclasses import asdict
    q = get_quote()
    print(json.dumps({"quote": asdict(q),
                      "route": asdict(decide_route(q, "USD", "EUR"))}, indent=2, default=str))

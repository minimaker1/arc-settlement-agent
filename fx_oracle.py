"""FX oracle: on-chain USDC/EURC implied rate vs real-world EUR/USD.

Reuses the read-only `arc_client`. Produces the basis the settlement agent uses
to choose the cheapest route for a cross-currency stablecoin payment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import arc_client
import config


@dataclass
class FxQuote:
    real_usd_per_eur: float | None
    onchain_usd_per_eur: float | None
    basis_pct: float | None                       # onchain / real - 1
    onchain_source: Literal["synthra_pool", "simulated"]


@dataclass
class Route:
    path: Literal["onchain_swap", "direct_usdc"]
    rationale: str
    est_savings_bps: float


def get_quote() -> FxQuote:
    """Read real EUR/USD and the on-chain USDC/EURC implied rate."""
    real = arc_client.real_eur_usd()
    pool = config.SYNTHRA_USDC_EURC_POOL
    if pool:
        snap = arc_client.pool_price(pool)
        # USDC sorts as token0 on Arc (0x3600.. < 0x89B5..), so token0-per-token1
        # is USD per EUR.
        onchain = (snap["token0_per_token1"] if snap["token0"]["symbol"] == "USDC"
                   else snap["token1_per_token0"])
        source: Literal["synthra_pool", "simulated"] = "synthra_pool"
    else:
        # No pool wired yet: simulate a small dislocation off the real rate so the
        # agent can be demoed end-to-end. Clearly labeled; replace once the pool
        # address is set in config / .env.
        onchain = round(real * 0.997, 6) if real else None  # ~30 bps cheap EURC
        source = "simulated"
    basis = (onchain / real - 1) if (onchain and real) else None
    return FxQuote(real, onchain, basis, source)


def decide_route(quote: FxQuote, send_ccy: str, recv_ccy: str) -> Route:
    """Pick the cheapest settlement path for a cross-currency payment.

    If the recipient wants EUR and EURC trades *below* spot on Arc (basis < 0),
    buying EURC on-chain beats converting at the real-world rate — capture the
    dislocation. Otherwise settle directly in USDC.
    """
    if recv_ccy == "EUR" and quote.basis_pct is not None and quote.basis_pct < 0:
        return Route(
            "onchain_swap",
            "EURC trades below spot on Arc — swap USDC->EURC on-chain for an FX edge",
            round(abs(quote.basis_pct) * 1e4, 1),
        )
    return Route(
        "direct_usdc",
        "No favorable on-chain dislocation — settle directly in USDC",
        0.0,
    )

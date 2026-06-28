"""FX-aware Settlement Agent — Track 4 (Agentic Economy) on Arc.

Given a cross-currency settlement intent, the agent:
  1. reads the on-chain USDC/EURC basis vs real EUR/USD (fx_oracle),
  2. chooses the cheapest route (on-chain swap vs direct USDC),
  3. settles in USDC via a Circle Developer-Controlled Wallet (dry_run default),
  4. attaches a memo (invoice / payout ref) — Arc transaction-memo style — and
     charges a tiny per-settlement fee (Nanopayments concept).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import arc_client
import config
import fx_oracle
from circle_wallet import CircleWallets


@dataclass
class SettlementIntent:
    amount: float
    send_ccy: str            # e.g. "USD"
    recv_ccy: str            # e.g. "EUR"
    to_address: str
    reference: str = ""      # invoice / payout id -> on-chain memo


def run(intent: SettlementIntent, dry_run: bool | None = None,
        collect_fee: bool = False) -> dict[str, Any]:
    """Plan and (dry-run) execute one cross-currency settlement.

    If `collect_fee` is set, the agent also collects a sub-cent pay-per-settlement
    nanopayment for the routing service it performed — a real on-chain micro-USDC
    transfer to its treasury (pay-per-call, RFB-02 style). Honors dry_run.
    """
    quote = fx_oracle.get_quote()
    route = fx_oracle.decide_route(quote, intent.send_ccy, intent.recv_ccy)
    wallet = CircleWallets(dry_run=dry_run)
    receipt = wallet.settle_usdc(intent.to_address, intent.amount, memo=intent.reference)
    out = {
        "intent": asdict(intent),
        "fx": asdict(quote),
        "route": asdict(route),
        "service_fee_usdc": config.NANOPAYMENT_FEE_USDC,
        "settlement": asdict(receipt),
    }
    if collect_fee and config.NANOPAY_SERVICE_ADDRESS:
        fee = wallet.settle_usdc(config.NANOPAY_SERVICE_ADDRESS,
                                 config.NANOPAYMENT_FEE_USDC,
                                 memo=f"nanopay:{intent.reference}")
        out["nanopayment"] = asdict(fee)
    return out


if __name__ == "__main__":
    import json

    print("Arc testnet block:", arc_client.block_number())
    demo = SettlementIntent(
        amount=1000.0, send_ccy="USD", recv_ccy="EUR",
        to_address="0x" + "1" * 40, reference="invoice-2026-0001",
    )
    print(json.dumps(run(demo), indent=2, default=str))

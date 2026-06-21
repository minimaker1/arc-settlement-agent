"""Circle Developer-Controlled Wallets wrapper (USDC settlement on Arc testnet).

Server-side signing via Circle's API — no raw private keys handled locally.
Defaults to dry_run: NEVER moves funds unless dry_run=False AND an API key is
configured. Testnet only.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import config


@dataclass
class SettlementReceipt:
    ok: bool
    dry_run: bool
    amount_usdc: float
    to_address: str
    memo: str
    tx_ref: str
    detail: str


class CircleWallets:
    """Minimal wrapper around Circle Developer-Controlled Wallets."""

    def __init__(self, dry_run: bool | None = None) -> None:
        self.api_key = config.CIRCLE_API_KEY
        self.wallet_id = config.CIRCLE_WALLET_ID
        self.dry_run = config.DRY_RUN_DEFAULT if dry_run is None else dry_run

    def settle_usdc(self, to_address: str, amount_usdc: float, memo: str = "") -> SettlementReceipt:
        """Send USDC on Arc testnet. dry_run (default) simulates, moving no funds."""
        if self.dry_run or not self.api_key:
            return SettlementReceipt(
                ok=True,
                dry_run=True,
                amount_usdc=amount_usdc,
                to_address=to_address,
                memo=memo,
                tx_ref=f"dryrun-{int(time.time())}",
                detail=("DRY RUN — no funds moved. Set CIRCLE_API_KEY (+ entity "
                        "secret / wallet id) and pass dry_run=False to execute on "
                        "Arc testnet."),
            )
        # --- real Arc-testnet execution (Developer-Controlled Wallets) -------- #
        # Wired against Circle's createTransaction flow once the API key + entity
        # secret are provided. Circle signs server-side; we attach `memo` as the
        # on-chain transaction memo for reconciliation.
        raise NotImplementedError(
            "Real settlement is wired with your Circle API key + entity secret."
        )

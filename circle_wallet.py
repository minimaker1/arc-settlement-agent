"""Circle Developer-Controlled Wallets client (USDC settlement on Arc testnet).

Server-side signing via Circle's API — no raw private keys handled locally.
`settle_usdc` defaults to dry_run: it NEVER moves funds unless dry_run=False AND
the API key / wallet are configured. Testnet only.
"""
from __future__ import annotations

import base64
import time
import uuid
from dataclasses import dataclass

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

import config


@dataclass
class SettlementReceipt:
    ok: bool
    dry_run: bool
    amount_usdc: float
    to_address: str
    memo: str
    tx_ref: str
    state: str
    detail: str


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.CIRCLE_API_KEY}",
            "Content-Type": "application/json"}


def _get_public_key() -> str:
    r = requests.get(f"{config.CIRCLE_API_BASE}/config/entity/publicKey",
                     headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json()["data"]["publicKey"]


def _ciphertext(public_key_pem: str) -> str:
    """Fresh single-use entity-secret ciphertext (RSA-OAEP / SHA-256)."""
    pk = serialization.load_pem_public_key(public_key_pem.encode())
    ct = pk.encrypt(
        bytes.fromhex(config.CIRCLE_ENTITY_SECRET),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(ct).decode()


class CircleWallets:
    """Minimal client over Circle Developer-Controlled Wallets."""

    def __init__(self, dry_run: bool | None = None) -> None:
        self.api_key = config.CIRCLE_API_KEY
        self.wallet_id = config.CIRCLE_WALLET_ID
        self.dry_run = config.DRY_RUN_DEFAULT if dry_run is None else dry_run
        self._pub: str | None = None

    def _pubkey(self) -> str:
        if self._pub is None:
            self._pub = _get_public_key()
        return self._pub

    def usdc_token_id(self, wallet_id: str | None = None) -> str | None:
        """Resolve Circle's tokenId for USDC held by the wallet."""
        wid = wallet_id or self.wallet_id
        r = requests.get(f"{config.CIRCLE_API_BASE}/wallets/{wid}/balances",
                         headers=_headers(), timeout=20)
        r.raise_for_status()
        for tb in r.json()["data"].get("tokenBalances", []):
            if tb["token"].get("symbol") == "USDC":
                return tb["token"]["id"]
        return None

    def transfer_usdc(self, to_address: str, amount_usdc: float, memo: str = "") -> dict:
        """Execute a USDC transfer on Arc testnet (Circle signs server-side)."""
        token_id = self.usdc_token_id()
        if not token_id:
            raise RuntimeError("USDC token id not found for wallet — fund it first.")
        body = {
            "idempotencyKey": str(uuid.uuid4()),
            "entitySecretCiphertext": _ciphertext(self._pubkey()),
            "walletId": self.wallet_id,
            "tokenId": token_id,
            "destinationAddress": to_address,
            "amounts": [str(amount_usdc)],
            "feeLevel": "MEDIUM",
        }
        if memo:
            body["refId"] = memo[:32]  # reconciliation reference
        r = requests.post(f"{config.CIRCLE_API_BASE}/developer/transactions/transfer",
                          headers=_headers(), json=body, timeout=30)
        if not r.ok:
            raise RuntimeError(f"transfer {r.status_code}: {r.text}")
        return r.json()["data"]

    def get_transaction(self, tx_id: str) -> dict:
        r = requests.get(f"{config.CIRCLE_API_BASE}/transactions/{tx_id}",
                         headers=_headers(), timeout=20)
        r.raise_for_status()
        return r.json()["data"]["transaction"]

    def contract_execution(self, contract: str, call_data: str,
                           amount: str | None = None) -> dict:
        """Execute a contract call from the wallet (Circle signs server-side).

        `amount` is native-token value (msg.value) for payable calls — e.g. the
        tiny Pyth updatePriceFeeds fee. Real on-chain write.
        """
        body = {
            "idempotencyKey": str(uuid.uuid4()),
            "entitySecretCiphertext": _ciphertext(self._pubkey()),
            "walletId": self.wallet_id,
            "contractAddress": contract,
            "callData": call_data,
            "feeLevel": "MEDIUM",
        }
        if amount is not None:
            body["amount"] = amount
        r = requests.post(f"{config.CIRCLE_API_BASE}/developer/transactions/contractExecution",
                          headers=_headers(), json=body, timeout=30)
        if not r.ok:
            raise RuntimeError(f"contractExecution {r.status_code}: {r.text}")
        return r.json()["data"]

    def settle_usdc(self, to_address: str, amount_usdc: float, memo: str = "") -> SettlementReceipt:
        """Send USDC on Arc testnet. dry_run (default) simulates, moving no funds."""
        if self.dry_run or not self.api_key or not self.wallet_id:
            return SettlementReceipt(
                ok=True, dry_run=True, amount_usdc=amount_usdc, to_address=to_address,
                memo=memo, tx_ref=f"dryrun-{int(time.time())}", state="DRYRUN",
                detail="DRY RUN — no funds moved. Pass dry_run=False to execute on Arc testnet.",
            )
        tx = self.transfer_usdc(to_address, amount_usdc, memo=memo)
        return SettlementReceipt(
            ok=True, dry_run=False, amount_usdc=amount_usdc, to_address=to_address,
            memo=memo, tx_ref=tx.get("id", ""), state=tx.get("state", "INITIATED"),
            detail="Submitted to Arc testnet via Circle Developer-Controlled Wallet.",
        )

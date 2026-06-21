"""Real end-to-end settlement demo on Arc testnet (1 USDC). Testnet only."""
from __future__ import annotations

import json
import time
import uuid

import requests

import agent
import arc_client
import config
from circle_wallet import CircleWallets, _ciphertext, _get_public_key, _headers

SENDER = "0x335c6c9824506c9e7fd2b28e62838a3374e6eece"


def _create_recipient() -> str:
    pub = _get_public_key()
    ws = requests.post(
        f"{config.CIRCLE_API_BASE}/developer/walletSets", headers=_headers(),
        json={"idempotencyKey": str(uuid.uuid4()), "entitySecretCiphertext": _ciphertext(pub),
              "name": "recipient-set"}, timeout=30,
    ).json()["data"]["walletSet"]["id"]
    w = requests.post(
        f"{config.CIRCLE_API_BASE}/developer/wallets", headers=_headers(),
        json={"idempotencyKey": str(uuid.uuid4()), "entitySecretCiphertext": _ciphertext(pub),
              "walletSetId": ws, "blockchains": ["ARC-TESTNET"], "count": 1,
              "accountType": "EOA"}, timeout=30,
    ).json()["data"]["wallets"][0]
    return w["address"]


def main() -> None:
    recipient = _create_recipient()
    print("recipient wallet:", recipient)

    res = agent.run(
        agent.SettlementIntent(amount=1.0, send_ccy="USD", recv_ccy="EUR",
                               to_address=recipient, reference="invoice-2026-0001"),
        dry_run=False,
    )
    print(json.dumps(res, indent=2, default=str))

    tx_id = res["settlement"]["tx_ref"]
    cw = CircleWallets(dry_run=False)
    for _ in range(12):
        tx = cw.get_transaction(tx_id)
        state = tx.get("state")
        print("tx state:", state, "| hash:", tx.get("txHash"))
        if state in ("COMPLETE", "CONFIRMED", "FAILED", "CANCELLED"):
            break
        time.sleep(5)

    print("\n-- on-chain balances (read via arc_client) --")
    print("sender   :", arc_client.erc20_balance(arc_client.USDC, SENDER) / 1e6, "USDC")
    print("recipient:", arc_client.erc20_balance(arc_client.USDC, recipient) / 1e6, "USDC")


if __name__ == "__main__":
    main()

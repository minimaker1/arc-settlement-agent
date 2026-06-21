"""One-time setup for Circle Developer-Controlled Wallets on Arc testnet.

Generates + registers an entity secret, creates a wallet set, and creates an
EOA wallet on ARC-TESTNET. Writes the entity secret + wallet id back to .env
(gitignored) and saves the recovery file. Idempotent where possible.

Testnet only. Run once: `python circle_setup.py`
"""
from __future__ import annotations

import base64
import secrets
import uuid
from pathlib import Path

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from dotenv import load_dotenv, set_key

import config

ENV = Path(__file__).parent / ".env"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.CIRCLE_API_KEY}",
            "Content-Type": "application/json"}


def get_public_key() -> str:
    r = requests.get(f"{config.CIRCLE_API_BASE}/config/entity/publicKey",
                     headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json()["data"]["publicKey"]


def encrypt_entity_secret(public_key_pem: str, entity_secret_hex: str) -> str:
    """RSA-OAEP (SHA-256) encrypt the 32-byte secret, base64 — single-use per request."""
    pk = serialization.load_pem_public_key(public_key_pem.encode())
    ct = pk.encrypt(
        bytes.fromhex(entity_secret_hex),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(ct).decode()


def main() -> None:
    load_dotenv(ENV)
    if not config.CIRCLE_API_KEY:
        raise SystemExit("CIRCLE_API_KEY missing in .env")

    pub = get_public_key()
    print("✓ entity public key fetched")

    # 1) entity secret (reuse if already in .env)
    entity_secret = config.CIRCLE_ENTITY_SECRET or secrets.token_hex(32)
    newly_generated = not config.CIRCLE_ENTITY_SECRET
    if newly_generated:
        set_key(str(ENV), "CIRCLE_ENTITY_SECRET", entity_secret)
        print("✓ entity secret generated -> .env")

        # 2) register it once
        ct = encrypt_entity_secret(pub, entity_secret)
        r = requests.post(
            f"{config.CIRCLE_API_BASE}/config/entity/entitySecret/register",
            headers=_headers(), json={"entitySecretCiphertext": ct}, timeout=30,
        )
        if r.ok:
            rec = (r.json().get("data") or {}).get("recoveryFile")
            if rec:
                Path(__file__).parent.joinpath("circle_recovery_file.dat").write_text(rec)
            print("✓ entity secret registered (recovery file saved)")
        else:
            print("! register:", r.status_code, r.text[:300])
    else:
        print("• reusing entity secret from .env")

    # 3) wallet set
    r = requests.post(
        f"{config.CIRCLE_API_BASE}/developer/walletSets", headers=_headers(),
        json={"idempotencyKey": str(uuid.uuid4()),
              "entitySecretCiphertext": encrypt_entity_secret(pub, entity_secret),
              "name": "arc-settlement-agent"}, timeout=30,
    )
    r.raise_for_status()
    wallet_set_id = r.json()["data"]["walletSet"]["id"]
    print("✓ wallet set:", wallet_set_id)

    # 4) wallet on ARC-TESTNET
    r = requests.post(
        f"{config.CIRCLE_API_BASE}/developer/wallets", headers=_headers(),
        json={"idempotencyKey": str(uuid.uuid4()),
              "entitySecretCiphertext": encrypt_entity_secret(pub, entity_secret),
              "walletSetId": wallet_set_id, "blockchains": ["ARC-TESTNET"],
              "count": 1, "accountType": "EOA"}, timeout=30,
    )
    r.raise_for_status()
    w = r.json()["data"]["wallets"][0]
    set_key(str(ENV), "CIRCLE_WALLET_ID", w["id"])
    print("✓ wallet id:", w["id"])
    print("✓ wallet address:", w["address"])
    print(f"\nFund via faucet (ARC-TESTNET, 10 USDC/hr): https://faucet.circle.com\n  -> {w['address']}")


if __name__ == "__main__":
    main()

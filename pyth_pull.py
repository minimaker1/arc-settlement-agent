"""Pyth pull-oracle flow on Arc — fetch a fresh update off-chain (Hermes), push
it on-chain (updatePriceFeeds), then read the now-fresh price.

For feeds not kept warm on Arc testnet (e.g. USD/KRW), the agent refreshes the
feed itself at settlement time — the canonical Pyth pull model, and the pattern
Arc's own Pyth guide describes ("fetch update data -> updatePriceFeeds -> read").
The push is a real on-chain write (payable; the fee is ~1 wei on Arc testnet)
via a Circle Developer-Controlled Wallet.
"""
from __future__ import annotations

import requests

import pyth
from circle_wallet import CircleWallets

HERMES = "https://hermes.pyth.network"
_SEL_GET_UPDATE_FEE = "0xd47eed45"      # getUpdateFee(bytes[])
_SEL_UPDATE_PRICE_FEEDS = "0xef9e5e28"  # updatePriceFeeds(bytes[])

# Feeds we refresh via pull (not kept warm on Arc testnet).
FEED = {"USD/KRW": "e539120487c29b4defdf9a53d337316ea022a2688978a468f9efd847201be7e3"}


def hermes_latest(feed_id: str) -> tuple[str, float, int]:
    """Return (update_blob_hex, price, publish_time) from Pyth Hermes."""
    r = requests.get(f"{HERMES}/v2/updates/price/latest",
                     params={"ids[]": feed_id}, timeout=20)
    r.raise_for_status()
    d = r.json()
    blob = d["binary"]["data"][0]
    p = d["parsed"][0]["price"]
    return blob, int(p["price"]) * 10 ** int(p["expo"]), int(p["publish_time"])


def _encode_bytes_array(blob_hex: str) -> str:
    """ABI-encode a single-element bytes[] (the Hermes update blob)."""
    b = bytes.fromhex(blob_hex)
    n = len(b)
    body = b + b"\x00" * ((-n) % 32)
    head = ((0x20).to_bytes(32, "big") + (1).to_bytes(32, "big")
            + (0x20).to_bytes(32, "big") + n.to_bytes(32, "big"))
    return (head + body).hex()


def get_update_fee(blob_hex: str) -> int:
    """Read-only: fee (native wei) required to push this update."""
    res = pyth._rpc_call(pyth.PYTH, _SEL_GET_UPDATE_FEE + _encode_bytes_array(blob_hex))
    return int(res, 16)


def push_update(blob_hex: str, dry_run: bool = True) -> dict:
    """Push a Pyth update on-chain via updatePriceFeeds (payable write)."""
    call_data = "0x" + _SEL_UPDATE_PRICE_FEEDS + _encode_bytes_array(blob_hex)
    fee = get_update_fee(blob_hex)
    if dry_run:
        return {"dry_run": True, "fee_wei": fee, "call_bytes": len(call_data) // 2 - 1,
                "detail": "DRY RUN — pass dry_run=False to push on Arc testnet."}
    # Pyth refunds excess msg.value; 1 gwei native is plenty over a ~1-wei fee.
    tx = CircleWallets(dry_run=False).contract_execution(pyth.PYTH, call_data,
                                                         amount="0.000000001")
    return {"dry_run": False, "fee_wei": fee, "tx": tx}


if __name__ == "__main__":
    blob, price, pub = hermes_latest(FEED["USD/KRW"])
    print(f"Hermes USD/KRW = {price:.2f}  publish {pub}  blob {len(blob)//2}B")
    print("push (dry-run):", push_update(blob, dry_run=True))

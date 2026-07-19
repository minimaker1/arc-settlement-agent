"""KRW1 / USDC corridor demo.

Settle a won-denominated payment at the *real on-chain* USD/KRW rate. Because the
USD/KRW feed isn't kept warm on Arc testnet, the agent uses Pyth's pull model: it
fetches the latest update from Hermes, pushes it on-chain (updatePriceFeeds), then
reads the now-fresh rate — and settles the equivalent USDC. This is the
version I actually want: Korean-won cross-border settlement at a transparent
on-chain rate instead of a bank's opaque FX spread.

Dry-run by default. `python demo_krw.py --live` pushes the update on-chain (a
real, ~1-wei write via a Circle Developer-Controlled Wallet) and reads the result.
"""
from __future__ import annotations

import sys

import pyth
import pyth_pull

KRW_ID = pyth_pull.FEED["USD/KRW"]


def quote(amount_krw: float, live: bool = False) -> None:
    blob, hermes_price, pub = pyth_pull.hermes_latest(KRW_ID)
    fee = pyth_pull.get_update_fee(blob)
    print(f"Hermes USD/KRW = {hermes_price:,.2f}   (push fee = {fee} wei, ~free)")

    if not live:
        rate, src = hermes_price, "hermes (dry-run; would push + read on-chain when live)"
    else:
        res = pyth_pull.push_update(blob, dry_run=False)
        print("pushed updatePriceFeeds ->", res["tx"].get("id"), res["tx"].get("state"))
        p = pyth.read_price(KRW_ID)               # now warm on-chain
        rate, src = p.price, f"on-chain Pyth (age {p.age_seconds:.0f}s)"

    usdc = amount_krw / rate
    print(f"\nSettle  ₩{amount_krw:,.0f}")
    print(f"  rate:  {rate:,.2f} KRW per USD   [{src}]")
    print(f"  -> pay {usdc:,.6f} USDC")
    # A bank typically charges ~1-2% on KRW FX; that spread on this amount:
    print(f"  (a ~1.5% bank FX spread on this would cost ~{usdc*0.015:,.4f} USDC extra)")


if __name__ == "__main__":
    live = "--live" in sys.argv
    quote(1_000_000, live=live)

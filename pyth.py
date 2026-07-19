"""Read Pyth price feeds on Arc testnet — read-only, no updates, no fees.

Pyth is a pull oracle, but its on-chain contract caches the latest price. We read
it directly with `getPriceUnsafe(bytes32)` via `eth_call` — no transaction, no
fee. Freshness is checked via `publishTime` (staleness) and uncertainty via the
confidence interval, which is exactly the confidence-gating a settlement agent
should do before acting on a price.

Pyth on Arc testnet: 0x2880aB155794e7179c9eE2e38200202908C17B43
Docs: https://docs.arc.io/arc/tools/oracles
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

RPC_URL = "https://rpc.testnet.arc.network"
PYTH = "0x2880aB155794e7179c9eE2e38200202908C17B43"
_SEL_GET_PRICE_UNSAFE = "0x96834ad3"  # getPriceUnsafe(bytes32)

# Pyth price-feed ids are global constants across every Pyth deployment.
# All three are live on the Arc testnet Pyth contract.
FEED = {
    "EUR/USD":  "a995d00bb36a63cef7fd2c287dc105fc8f3d93779f062f09551b0af3e81ec30b",  # FX
    "EURC/USD": "76fa85158bf14ede77087fe3ae472f66213f6ea2f5b411cb2de472794990fa5c",  # crypto
    "USDC/USD": "eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a",  # crypto
}


@dataclass
class PythPrice:
    feed: str
    price: float          # human price = raw * 10**expo
    conf: float           # confidence interval, same units as price
    expo: int
    publish_time: int     # unix seconds
    age_seconds: float

    @property
    def rel_conf_bps(self) -> float:
        return (self.conf / self.price) * 1e4 if self.price else float("inf")

    # Testnet-tuned: on Arc testnet the FX feed refreshes in seconds but the
    # stablecoin crypto feeds update every few hours, so we allow up to 12h here
    # and always surface the real age. On mainnet, tighten max_age to seconds.
    def is_usable(self, max_age_s: float = 43_200, max_conf_bps: float = 30) -> bool:
        """Fresh enough and tight enough to act on."""
        return self.age_seconds <= max_age_s and self.rel_conf_bps <= max_conf_bps


def _rpc_call(to: str, data: str) -> str:
    r = requests.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                     "params": [{"to": to, "data": data}, "latest"]}, timeout=15)
    r.raise_for_status()
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"eth_call reverted: {j['error']}")
    return j["result"]


def _sint(word: str) -> int:
    """Decode a 32-byte ABI word as a signed integer (int64/int32 are sign-
    extended across the full 256 bits, so decode at 256-bit width)."""
    v = int(word, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def read_price(feed_id_hex: str) -> PythPrice:
    """Read a Pyth feed's latest cached price from Arc testnet (getPriceUnsafe)."""
    data = _SEL_GET_PRICE_UNSAFE + feed_id_hex.replace("0x", "")
    res = _rpc_call(PYTH, data)
    h = res[2:]
    w = [h[i:i + 64] for i in range(0, len(h), 64)]           # price, conf, expo, publishTime
    expo = _sint(w[2])
    price = _sint(w[0]) * (10 ** expo)
    conf = int(w[1], 16) * (10 ** expo)
    pub = int(w[3], 16)
    return PythPrice(feed_id_hex, price, conf, expo, pub, time.time() - pub)


def eur_usd() -> PythPrice:
    return read_price(FEED["EUR/USD"])


def eurc_usd() -> PythPrice:
    return read_price(FEED["EURC/USD"])


def usdc_usd() -> PythPrice:
    return read_price(FEED["USDC/USD"])


if __name__ == "__main__":
    for name, fn in (("EUR/USD", eur_usd), ("EURC/USD", eurc_usd), ("USDC/USD", usdc_usd)):
        p = fn()
        print(f"{name:8s} = {p.price:.5f}  ±{p.conf:.5f}  ({p.rel_conf_bps:.1f} bps)  "
              f"age {p.age_seconds:.0f}s  usable={p.is_usable()}")

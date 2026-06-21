"""Minimal read-only client for Arc (Circle's stablecoin L1) testnet.

Raw JSON-RPC over `requests` only — no web3 dependency, no signing, no txs.
Mirrors the style of `hl_client.py`: read-only `eth_call` / `eth_*` endpoints.

Used to track the on-chain USDC/EURC (and future partner-stablecoin) FX basis
on Arc DEX pools vs. real-world FX, i.e. the Arc analogue of `krx_client` +
`basis-monitor`.

Arc testnet:
  RPC      https://rpc.testnet.arc.network
  chainId  5042002 (0x4cef52)
  explorer https://testnet.arcscan.app
  USDC     0x3600000000000000000000000000000000000000  (6-dec ERC-20 iface)
  EURC     0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a  (6 dec)

Docs: https://docs.arc.io/arc/references/contract-addresses
"""
from __future__ import annotations

from typing import Any

import requests

RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002

USDC = "0x3600000000000000000000000000000000000000"
EURC = "0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a"

# Uniswap-V3-style function selectors (Synthra is a V3 fork).
_SEL = {
    "symbol":   "0x95d89b41",
    "decimals": "0x313ce567",
    "balanceOf": "0x70a08231",
    "slot0":    "0x3850c7bd",
    "token0":   "0x0dfe1681",
    "token1":   "0xd21220a7",
    "fee":      "0xddca3f43",
    "getPool":  "0x1698ee82",  # factory.getPool(address,address,uint24)
}

_Q96 = 2 ** 96


# --------------------------------------------------------------------------- #
# JSON-RPC plumbing
# --------------------------------------------------------------------------- #
def _rpc(method: str, params: list[Any]) -> Any:
    r = requests.post(
        RPC_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=15,
    )
    r.raise_for_status()
    res = r.json()
    if "error" in res:
        raise RuntimeError(f"rpc error {method}: {res['error']}")
    return res["result"]


def _call(to: str, data: str) -> str:
    """eth_call returning raw hex (no decoding)."""
    return _rpc("eth_call", [{"to": to, "data": data}, "latest"])


# --------------------------------------------------------------------------- #
# Minimal ABI helpers (encode/decode only what we need)
# --------------------------------------------------------------------------- #
def _enc_addr(addr: str) -> str:
    return addr.lower().replace("0x", "").rjust(64, "0")


def _enc_uint(x: int) -> str:
    return f"{x:064x}"


def _words(hexstr: str) -> list[str]:
    """Split 0x-prefixed return data into 32-byte (64-hex) words."""
    h = hexstr[2:] if hexstr.startswith("0x") else hexstr
    return [h[i:i + 64] for i in range(0, len(h), 64)]


def _dec_uint(word: str) -> int:
    return int(word, 16)


def _dec_int(word: str, bits: int = 256) -> int:
    v = int(word, 16)
    if v >= 1 << (bits - 1):
        v -= 1 << bits
    return v


def _dec_addr(word: str) -> str:
    return "0x" + word[-40:]


def _dec_string(hexstr: str) -> str:
    """Decode an ABI-encoded dynamic string return value."""
    w = _words(hexstr)
    if len(w) < 2:
        # Some tokens return a bytes32 symbol instead of a string.
        return bytes.fromhex(w[0]).rstrip(b"\x00").decode("utf-8", "replace")
    length = _dec_uint(w[1])
    raw = "".join(w[2:])
    return bytes.fromhex(raw[: length * 2]).decode("utf-8", "replace")


# --------------------------------------------------------------------------- #
# Chain / ERC-20 reads
# --------------------------------------------------------------------------- #
def chain_id() -> int:
    return int(_rpc("eth_chainId", []), 16)


def block_number() -> int:
    return int(_rpc("eth_blockNumber", []), 16)


def erc20_symbol(token: str) -> str:
    return _dec_string(_call(token, _SEL["symbol"]))


def erc20_decimals(token: str) -> int:
    return _dec_uint(_words(_call(token, _SEL["decimals"]))[0])


def erc20_balance(token: str, holder: str) -> int:
    data = _SEL["balanceOf"] + _enc_addr(holder)
    return _dec_uint(_words(_call(token, data))[0])


# --------------------------------------------------------------------------- #
# Uniswap-V3-style pool reads (Synthra)
# --------------------------------------------------------------------------- #
def pool_tokens(pool: str) -> tuple[str, str, int]:
    """(token0, token1, fee) for a V3 pool."""
    t0 = _dec_addr(_words(_call(pool, _SEL["token0"]))[0])
    t1 = _dec_addr(_words(_call(pool, _SEL["token1"]))[0])
    fee = _dec_uint(_words(_call(pool, _SEL["fee"]))[0])
    return t0, t1, fee


def pool_slot0(pool: str) -> dict[str, int]:
    """Return sqrtPriceX96 + current tick from a V3 pool's slot0()."""
    w = _words(_call(pool, _SEL["slot0"]))
    return {"sqrt_price_x96": _dec_uint(w[0]), "tick": _dec_int(w[1])}


def factory_get_pool(factory: str, token_a: str, token_b: str, fee: int) -> str | None:
    """Look up a pool address from a V3 factory; None if unset (zero address)."""
    data = _SEL["getPool"] + _enc_addr(token_a) + _enc_addr(token_b) + _enc_uint(fee)
    addr = _dec_addr(_words(_call(factory, data))[0])
    return None if int(addr, 16) == 0 else addr


def price_from_sqrt(sqrt_price_x96: int, dec0: int, dec1: int) -> float:
    """token1-per-token0 in human units, from a V3 sqrtPriceX96."""
    raw = (sqrt_price_x96 / _Q96) ** 2  # token1_raw per token0_raw
    return raw * (10 ** (dec0 - dec1))


def pool_price(pool: str) -> dict[str, Any]:
    """Full price snapshot for a V3 pool: both directions, with symbols."""
    t0, t1, fee = pool_tokens(pool)
    d0, d1 = erc20_decimals(t0), erc20_decimals(t1)
    s = pool_slot0(pool)
    p10 = price_from_sqrt(s["sqrt_price_x96"], d0, d1)  # token1 per token0
    return {
        "pool": pool,
        "fee": fee,
        "token0": {"address": t0, "symbol": erc20_symbol(t0), "decimals": d0},
        "token1": {"address": t1, "symbol": erc20_symbol(t1), "decimals": d1},
        "tick": s["tick"],
        "token1_per_token0": p10,
        "token0_per_token1": (1 / p10) if p10 else None,
    }


# --------------------------------------------------------------------------- #
# FX basis: on-chain USDC/EURC vs real-world EUR/USD
# --------------------------------------------------------------------------- #
def fx_basis(onchain_usd_per_eur: float, real_usd_per_eur: float) -> dict[str, float | None]:
    """Basis between the on-chain implied USD/EUR and the real-world rate.

    Mirrors `krx_client.basis_vs_perp`. Positive basis_pct => EURC is rich on
    Arc vs spot FX (sell EURC / buy USDC side), negative => EURC cheap.
    """
    if not (onchain_usd_per_eur and real_usd_per_eur):
        return {"basis_pct": None, "onchain_usd_per_eur": onchain_usd_per_eur,
                "real_usd_per_eur": real_usd_per_eur}
    return {
        "onchain_usd_per_eur": onchain_usd_per_eur,
        "real_usd_per_eur": real_usd_per_eur,
        "basis_pct": onchain_usd_per_eur / real_usd_per_eur - 1,
    }


def real_eur_usd() -> float | None:
    """Real-world USD per EUR via yfinance (EURUSD=X). Imported lazily so the
    on-chain client works even where yfinance is unavailable."""
    try:
        import yfinance as yf
        h = yf.Ticker("EURUSD=X").history(period="5d", auto_adjust=False)
        h = h.dropna(subset=["Close"])
        return float(h["Close"].iloc[-1]) if len(h) else None
    except Exception:
        return None


if __name__ == "__main__":
    import json

    print("chainId   :", chain_id(), "(expected 5042002)")
    print("block     :", block_number())
    for tok, name in ((USDC, "USDC"), (EURC, "EURC")):
        print(f"{name:5s}    : symbol={erc20_symbol(tok)} decimals={erc20_decimals(tok)}")

    # Fill SYNTHRA_USDC_EURC_POOL once the pool address is known (from the
    # Synthra UI/factory) to unlock the live FX-basis snapshot below.
    pool = None
    if pool:
        snap = pool_price(pool)
        usd_per_eur = snap["token0_per_token1"] if snap["token0"]["symbol"] == "USDC" \
            else snap["token1_per_token0"]
        basis = fx_basis(usd_per_eur, real_eur_usd())
        print(json.dumps({"pool": snap, "fx_basis": basis}, indent=2))
    else:
        print("\n[pool unset] set the Synthra USDC/EURC pool address to enable "
              "the on-chain FX-basis snapshot.")

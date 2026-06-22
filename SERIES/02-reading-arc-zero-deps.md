# Part 2 — Reading Arc with zero dependencies

The pricing side of my settlement agent only needs to *read* Arc, so I kept it
deliberately tiny: no web3 library, just `requests` and raw JSON-RPC `eth_call`.

USDC and EURC are ERC-20s at documented addresses on Arc testnet:

- RPC: `https://rpc.testnet.arc.network` (chainId `5042002`)
- USDC: `0x3600000000000000000000000000000000000000`
- EURC: `0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a`

Reading a token's symbol/decimals is just a function selector + a tiny ABI
decode:

```python
def _call(to, data):
    r = requests.post(RPC_URL, json={"jsonrpc":"2.0","id":1,
        "method":"eth_call","params":[{"to":to,"data":data},"latest"]})
    return r.json()["result"]

def erc20_decimals(token):
    return int(_call(token, "0x313ce567")[2:], 16)   # decimals()
```

That worked first try against the documented addresses — no SDK, no setup. For
a Uniswap-V3-style pool I read `slot0()` and derive the price from
`sqrtPriceX96`; for the real-world leg I pull EUR/USD from a spot feed and
compute the basis as `onchain/real - 1`.

Two Arc details that made this pleasant:

- **USDC is the gas token.** No separate native-token funding step to read or
  later to settle — fees are denominated in dollars.
- **Deterministic, sub-second finality.** When I later settled on-chain, the
  receipt was trivial to reason about: it's final, not "probably final."

The whole read client is ~150 lines and has no dependencies beyond `requests`.
Sometimes the right amount of abstraction is none.

Code: https://github.com/minimaker1/arc-settlement-agent (`arc_client.py`)

*Part 2 of 5.*

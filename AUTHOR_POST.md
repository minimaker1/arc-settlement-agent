# Arc House guest post (Author = 200 pts)

Post in Arc House → Content/Blogs as a guest post (or the forum). Genuine build
writeup. Paste from the divider down.

---

## Building an FX-aware Settlement Agent on Arc

I build arbitrage and FX tooling, so when I looked at Arc the thing that jumped
out wasn't payments per se — it was that two stablecoins trading against each
other on-chain (USDC/EURC) imply an FX rate that can drift from the real-world
rate. If you're settling a cross-currency payment, converting at naive spot
leaves money on the table whenever that on-chain rate is off. So I built a small
agent that prices the route before it pays.

**What it does**
1. Reads the real EUR/USD rate and the on-chain USDC/EURC rate on Arc.
2. Computes the basis. If EURC trades below spot, routing the payment through an
   on-chain swap beats converting at the real rate — so the agent takes that path.
3. Settles in USDC via a Circle Developer-Controlled Wallet, attaching a memo
   (invoice / payout ref) for reconciliation, and charges a tiny per-settlement
   fee (Nanopayments-style).

**It actually settles on-chain.** Here's a real run on Arc testnet — 1 USDC,
FX-aware route, server-side signed by a Circle Dev-Controlled Wallet, no private
keys touched by my code:
`0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f`
(testnet.arcscan.app). Sub-second finality made verifying the receipt trivial.

**Why Arc fit well:** USDC-as-gas removed the usual native-token funding dance;
reading state over plain JSON-RPC against the documented USDC/EURC addresses
worked first try; and Developer-Controlled Wallets gave me autonomous settlement
without ever handling a key — exactly the trust model an agent needs.

**A couple of rough edges I hit** (and worked around): the raw `transfer` REST
endpoint wants a top-level `feeLevel`, not the SDK-style nested `fee` object;
and entity-secret registration is Console-only (the REST path 404s), which is
worth flagging for anyone scripting setup end-to-end.

Stack is Python, ~300 lines, read-only RPC + Circle Wallets. Next I want to wire
a live USDC/EURC pool to replace the simulated FX leg, and extend the routing to
StableFX corridors — a KRW1/USDC corridor in particular, since I'm in Korea.

Happy to share notes with anyone building payment/FX routing on Arc.

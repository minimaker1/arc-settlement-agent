# Part 1 — Why I built an FX-aware settlement agent on Arc

I come from FX and arbitrage — perp DEXs, CEXs, Korean equities. So when I
started poking at Arc, the thing that caught my eye wasn't payments in the
abstract. It was this: the moment two stablecoins trade against each other
on-chain (USDC/EURC), they imply an FX rate. And an implied on-chain rate can
drift from the real-world EUR/USD rate.

If you're settling a cross-currency payment and you convert at the naive spot
rate, you leave money on the table every time the on-chain rate is off-peg. A
remittance app, a marketplace paying global sellers, an agent buying a service
priced in euros — all of them quietly overpay when they ignore the basis.

So I built a small agent that **prices the route before it pays**:

1. Read the real EUR/USD rate and the on-chain USDC/EURC rate on Arc.
2. Compute the basis. If EURC trades below spot, buying EURC on-chain beats
   converting at the real rate — so route through the swap and capture it.
   Otherwise, settle directly in USDC.
3. Settle in USDC via a Circle Developer-Controlled Wallet, attach a memo for
   reconciliation, and charge a sub-cent per-settlement fee.

It runs autonomously, per payment. That's the whole idea: turn Arc's
stablecoin-FX rails into measurable savings instead of treating FX as a fixed
cost.

I built it for the Stablecoins Commerce Stack Challenge (Track 4, Agentic
Economy). Over the next few posts I'll go through how it actually works —
reading Arc with zero dependencies, settling without ever holding a private key,
the gotchas I hit, and where I want to take it next (including a KRW1/USDC
corridor, since I'm in Korea).

Code is open (MIT): https://github.com/minimaker1/arc-settlement-agent

*Part 1 of 5.*

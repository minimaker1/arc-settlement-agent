# Circle Developer Grants — application draft

Apply at https://circle.questbook.app/ (Circle Developer Grants). Milestone-based
USDC funding. Paste the sections into the matching form fields; adjust the ask if
the form suggests a range.

---

**Project name**
> FX-aware Settlement Agent

**One-liner**
> An autonomous agent that settles cross-currency stablecoin payments at the best
> available on-chain rate on Arc — and charges a sub-cent nanopayment per settlement.

**Which focus area(s)**
> Stablecoin FX · Agentic economic activity · Cross-border / P2P payments

**Problem**
> Cross-currency payments settle at the naive spot rate, so payers overpay whenever
> a stablecoin (e.g. EURC) drifts from the currency it's pegged to. On a €1M B2B
> settlement, a 30 bps dislocation is ~$3,000 left on the table. Nobody prices that
> gap before paying — and as AI agents begin settling autonomously, the leakage
> scales with them. Cross-border rails also still hide a 1–2% bank FX spread.

**Solution / what it does**
> The agent prices the route before it pays. It reads three live Pyth feeds on Arc
> (EUR/USD, EURC/USD, USDC/USD), measures how far EURC trades from its euro peg, and
> routes each payment the cheaper way — buy discounted EURC on-chain or settle direct
> in USDC — gated by a confidence + staleness check. It settles in USDC via a Circle
> Developer-Controlled Wallet (server-side signing, no private keys in the app) with a
> memo for reconciliation, and collects a per-settlement nanopayment for the service.
> A 🇰🇷 KRW1/USDC corridor uses Pyth's pull model: the agent refreshes USD/KRW on-chain
> itself, then settles won at a transparent on-chain rate instead of a bank spread.

**Why USDC + Circle are core (platform alignment)**
> USDC is the settlement rail and the nanopayment unit; Circle Developer-Controlled
> Wallets are what make autonomous settlement safe (no raw keys in the app). The
> design uses USDC-as-gas on Arc, transaction memos, and is built to extend into
> StableFX and Nanopayments. Circle products aren't a bolt-on — they are the trust
> and settlement layer the whole agent stands on.

**What we've shipped (execution evidence)**
> - Working agent on Arc testnet, fully on-chain pricing via Pyth (no simulated data).
> - Real on-chain USDC settlement via a Circle Developer-Controlled Wallet — verified
>   tx 0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f.
> - KRW1/USDC corridor via Pyth pull (agent pushes USD/KRW on-chain, then settles).
> - Public demo deployed: https://fx-aware-settlement-agent.onrender.com/present
> - Open source (MIT), zero-dependency Arc reader + reusable Circle-wallet helpers.

**What we'll ship next (proposed milestones)**
> - **M1 — Production hardening ($8k):** depth/slippage-aware confidence checks,
>   mainnet-ready wallet flows, monitoring + reconciliation, and a settlement SDK so
>   other apps/agents can call the router in a few lines.
> - **M2 — KRW1 corridor live + first users ($7k):** settle into KRW1 end-to-end once
>   it's on Arc; onboard 2–3 pilot payers (remittance / marketplace payout) and report
>   real settlement volume.
> - **M3 — Agent-to-agent + revenue ($5k):** expose the router as a paid service other
>   agents call, billed per settlement via Nanopayments; publish volume + fee metrics.

**Funding requested**
> $20,000 USDC, milestone-based (M1 $8k / M2 $7k / M3 $5k).

**Path to adoption & revenue**
> Revenue is built in: a per-settlement nanopayment (the agent monetizes the routing
> it performs). Adoption path: settlement-as-a-service SDK/API → pilot payers in
> cross-border/payout flows → agent-to-agent usage. The KRW1 corridor opens a
> concrete Korean-market wedge with quantifiable savings vs bank FX spreads.

**Team / technical ownership**
> Jeong-hun Park (solo) — Korea-based quant; background in FX, basis, and funding-rate
> arbitrage across perp DEXs, CEXs, and Korean equities. Built the entire agent solo
> (see repo history): raw-JSON-RPC Arc reader, Pyth integration (read + pull), Circle
> Dev-Controlled Wallet settlement, the web demo, and the KRW corridor.

**Ecosystem impact**
> Expands USDC utility into FX-aware settlement and a new geography (Korean won),
> turns Arc's stablecoin-FX rails into measurable savings, and ships open-source
> primitives (Arc reader, Pyth pull helper, Circle-wallet settlement) other Arc
> builders can lift directly.

**Links**
> - Code (MIT): https://github.com/minimaker1/arc-settlement-agent
> - Live demo: https://fx-aware-settlement-agent.onrender.com/present
> - Deck: https://github.com/minimaker1/arc-settlement-agent/blob/master/deck.pdf
> - Circle Developer account email: changepa@gmail.com

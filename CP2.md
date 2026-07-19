# Encode CP2 (Mid-submission) — ready to paste

Encode CP2 opens **Mon Jul 20, 8:59 PM KST** and closes **Jul 27**. Submit from
the project page: https://www.encodeclub.com/my-programmes/arc-hackathon
(WIP is fine at this checkpoint — repo link + progress summary.)

---

**Repository:** https://github.com/minimaker1/arc-settlement-agent
**Live demo:** https://fx-aware-settlement-agent.onrender.com/present

**Progress since CP1** — FX-aware Settlement Agent (DeFi + Agentic Economy):

- FX pricing is now **fully on-chain via Pyth on Arc** (EUR/USD, EURC/USD,
  USDC/USD) with a confidence + staleness gate; the agent routes on the real
  EURC-vs-EUR-peg basis. No simulated data.
- Added a **KRW1/USDC corridor using Pyth's pull model**: the agent fetches the
  USD/KRW update from Hermes, pushes it on-chain (`updatePriceFeeds`) via a Circle
  Developer-Controlled Wallet, then reads and settles. Verified USD/KRW live on Arc.
- **Real on-chain settlement** executed (Circle Dev-Controlled Wallet: USDC +
  memo) plus a per-settlement nanopayment.
- **Public demo deployed** (Render), planning with live Pyth data; real on-chain
  execution runs locally with keys.

**Next (to final):** confidence-check refinements, pitch deck, and a demo video.

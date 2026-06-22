# YouTube upload text (copy-paste)

**Visibility:** Unlisted (paste the link into the hackathon form).

---

### Title
FX-aware Settlement Agent on Arc — Stablecoins Commerce Stack Challenge (Track 4)

### Description
An autonomous agent that settles cross-currency stablecoin payments at the best
available on-chain rate on Arc (Circle's stablecoin L1).

It reads the live on-chain USDC/EURC rate on Arc, compares it to the real-world
EUR/USD rate, routes each payment the cheaper way (on-chain swap vs. direct USDC)
instead of converting at naive spot, then settles in USDC via a Circle
Developer-Controlled Wallet — with a memo for reconciliation.

In this demo:
• Plan a settlement → the agent reads FX, computes the basis, and picks the route
• Execute → a real 1 USDC settlement on Arc testnet, signed server-side by a
  Circle Developer-Controlled Wallet (no private keys handled by the app)
• Verify → the live transaction on the Arc block explorer

Built with: USDC · Circle Developer-Controlled Wallets · Nanopayments · USDC-as-gas
on Arc.

Code (open source, MIT): https://github.com/minimaker1/arc-settlement-agent
On-chain proof: https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f

Submission for The Stablecoins Commerce Stack Challenge (Arc / Circle), Track 4 —
Agentic Economy. Educational / testnet demo only.

#Arc #Circle #USDC #stablecoins #onchain #agenticpayments

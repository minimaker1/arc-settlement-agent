# Demo Video Script (~2.5 min)

Setup before recording:
- Terminal 1: `cd ~/arc-settlement-agent && /Users/macmini/아비트라지/venv/bin/python web.py`
- Browser tab A: http://localhost:8000
- Browser tab B: https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f
- (Optional) README.md open to the mermaid diagram.

Record screen + voiceover. Beats:

**0:00 – 0:20 · Intro**
> "Hi, I'm Mihwa. This is the FX-aware Settlement Agent, built on Arc for Track 4,
> the Agentic Economy. It's an agent that settles cross-currency stablecoin
> payments at the best on-chain rate, autonomously."

**0:20 – 0:40 · Problem**
> "Cross-border and agentic commerce constantly convert currencies. Converting at
> naive spot leaves money on the table whenever a stablecoin like EURC trades
> off-peg on-chain. My agent prices the route before it pays."

**0:40 – 1:25 · Live demo (tab A)**
> "I enter a 1,000 USD payment to a EUR recipient and hit Plan settlement."
> (click) "The agent reads the real EUR/USD rate and the on-chain USDC/EURC rate
> on Arc, computes the basis — here EURC is ~30 bps cheap — so it routes via an
> on-chain swap to capture that FX edge, then settles in USDC with a memo for
> reconciliation. The web demo plans in dry-run so no funds move."

**1:25 – 2:00 · Real on-chain settlement (tab B)**
> "But it really executes. Here's a real settlement this agent made on Arc testnet
> via a Circle Developer-Controlled Wallet — one USDC, signed server-side, no
> private keys handled by my code. Confirmed on arcscan with sub-second finality."

**2:00 – 2:25 · Architecture + Circle products**
> "Under the hood: a read-only Arc RPC client feeds the FX oracle, the agent makes
> the route decision, and Circle Wallets settle the USDC leg. Built on USDC,
> Circle Developer-Controlled Wallets, and Nanopayments for per-settlement fees —
> with USDC as gas on Arc."

**2:25 – 2:35 · Close**
> "FX-aware settlement turns Arc's stablecoin rails into measurable savings, per
> payment, autonomously. Thanks for watching."

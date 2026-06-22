# Demo Video Script (~2.5 min)

## Recommended: captioned mode (no voiceover, no editing)

Captions are built into the demo page — record the screen and the subtitles are
baked into the video.

1. Start server: `cd ~/arc-settlement-agent && /Users/macmini/아비트라지/venv/bin/python web.py`
2. Open **http://localhost:8000/present** (full screen).
3. Start screen recording: **Cmd+Shift+5 → Record Entire/Selected Screen**.
4. Walk the captions with the **▶** button (bottom bar, 8 steps), pausing ~3–6 s each:
   - Steps 1–3: intro / problem / setup. At step 3, **click "Plan settlement"**
     (the result fills in and the caption auto-jumps to step 4).
   - Steps 4–5: the FX basis, route, and dry-run settlement are on screen.
   - Step 6: **click the green panel's arcscan link** to show the real on-chain tx,
     then come back.
   - Steps 7–8: stack / Circle products / closing line.
5. Stop recording (menu-bar stop). Upload to YouTube (unlisted) or Loom → copy link.

That's it — ~2.5 min, captions visible throughout, nothing to edit.

---

## Voiceover script (optional, if you'd rather narrate)

Setup: server running, tab A = http://localhost:8000, tab B = the arcscan tx.
Beats:

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

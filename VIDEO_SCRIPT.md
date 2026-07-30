# Demo Video Script (~3 min) — captioned, no voiceover, no editing

Captions are baked into the demo page, so you just screen-record and click ▶.

## Setup
- Open the demo: **https://fx-aware-settlement-agent.onrender.com/present**
  (or local: `python web.py` → http://localhost:8000/present)
- (For the KRW beat) a terminal ready to run:
  `python demo_krw.py --live`
- Start screen recording (Cmd+Shift+5 → Record Entire Screen).

## Walk the 8 captions with the ▶ button (~15–25s each)

1. **Intro** — title + tracks (DeFi + Agentic Economy).
2. **Problem** — payments convert at naive spot; stablecoins drift from peg.
3. **Setup the settlement** — 1,000 USD → EUR recipient. **Click “Plan settlement.”**
   (The result fills in and the caption auto-advances to step 4.)
4. **Pricing** — three live **Pyth** feeds on Arc (EUR/USD, EURC/USD, USDC/USD);
   the basis = how far EURC is from its euro peg is on screen.
5. **Route + safety** — basis picks on-chain swap vs direct USDC; the confidence +
   staleness gate is shown. Dry-run, no funds move.
6. **Real settlement** — **click the green panel’s arcscan link** to show the real
   on-chain USDC settlement (Circle Dev-Controlled Wallet). Come back.
7. **🇰🇷 KRW corridor** — switch to the terminal and run **`python demo_krw.py --live`**:
   it fetches USD/KRW from Hermes, pushes it on-chain (Pyth pull), reads the fresh
   rate, and quotes ₩1,000,000 → ~672 USDC. (Optional but strong — shows the pull model.)
8. **Close** — real Pyth pricing, real settlement, live demo, open source.

Stop recording → upload (YouTube unlisted / Loom) → replace the video link in
SUBMISSION.md / SUBMISSION_LEPTON.md and the Encode final submission.

---

## Voiceover alternative (if you'd rather narrate)
Same beats; talk over the /present page + the arcscan tx + the `demo_krw.py` run.
Keep it under 3 minutes and focus on: Pyth on-chain pricing → route → real Circle
settlement → the KRW pull corridor.

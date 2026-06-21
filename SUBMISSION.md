# Submission Packet — The Stablecoins Commerce Stack Challenge

Copy each field into the submission form at
https://challenges.ignyte.ae/competition/4B436318-C737-F111-9A49-6045BD14D400
(My Submissions → Submit). Deadline: **July 13, 2026**.

---

**Title**
> FX-aware Settlement Agent

**Short description**
> An autonomous agent that settles cross-currency stablecoin payments at the best
> available on-chain rate on Arc. It reads the live USDC/EURC basis, routes each
> payment the cheaper way (on-chain swap vs. direct USDC) instead of converting
> at naive spot, and settles in USDC via a Circle Developer-Controlled Wallet
> with a transaction memo for reconciliation.

**Track**
> Track 4 — Best Agentic Economy Experience on Arc

**Email (Circle Developer Account)**
> changepa@gmail.com   ← confirm this is the email on console.circle.com

**Circle products used on Arc** (tick these)
> ✅ USDC   ✅ Wallets (Developer-Controlled)   ✅ Nanopayments (per-settlement fee concept)
> StableFX — referenced as the routing target (gated; conceptual integration)

**Functional MVP + architecture diagram**
> - Backend: `agent.py` (orchestration) + `fx_oracle.py` (on-chain basis vs spot)
>   + `circle_wallet.py` (Circle Dev-Controlled Wallets) + `arc_client.py`
>   (read-only Arc RPC). Frontend: `web.py` (one-page UI, no deps).
> - Architecture diagram: see README.md (mermaid).
> - Runs live against Arc testnet (chainId 5042002).

**Video demonstration**
> <PASTE VIDEO LINK>   (script in VIDEO_SCRIPT.md; ~2.5 min)

**GitHub / code repository**
> <PASTE REPO LINK>   (see TOMORROW.md for one-command publish; .env is gitignored)

**Demo application URL**
> Runs locally: `python web.py` → http://localhost:8000  (shown in the video).
> Optional public URL via `ngrok http 8000` — see TOMORROW.md.

**Circle Product Feedback** (required section)
> *Why these products:* USDC + Developer-Controlled Wallets let the agent settle
> autonomously with server-side signing — we never handle a private key, which is
> the exact trust model an agentic payment system needs. USDC-as-gas on Arc removes
> the native-token funding step. Nanopayments fits per-settlement pricing.
>
> *What worked well:* Reading Arc over plain JSON-RPC worked first try against the
> documented USDC/EURC addresses. Dev-controlled wallet provisioning (entity secret
> → wallet set → ARC-TESTNET wallet) and the testnet faucet were smooth, and
> deterministic sub-second finality made settlement receipts trivial to verify
> (confirmed our 1-USDC tx on arcscan immediately).
>
> *What could be improved:* (1) The `transfer` API rejects the SDK-style nested
> `fee:{type:'level',config:{feeLevel}}` — the raw REST endpoint needs a top-level
> `feeLevel`; the error pointed at gasPrice/gasLimit, which was confusing. (2)
> Entity-secret registration is Console-only — there's no documented REST endpoint
> (`/config/entity/entitySecret/register` returns 404), which trips up fully
> programmatic setup. (3) DEX pool addresses (e.g. Synthra USDC/EURC) aren't
> discoverable from the docs or the Uniswap registry, so wiring an on-chain price
> source needs UI hunting.
>
> *Recommendations:* Document the raw-REST `feeLevel` shape explicitly; expose a
> REST entity-secret registration path (or clearly flag it as Console-only in the
> quickstart); and publish a machine-readable testnet registry of DEX/pool
> addresses (and StableFX corridors as they launch) so oracle/routing builders can
> integrate programmatically.

---

**On-chain proof:** tx `0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f`
https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f

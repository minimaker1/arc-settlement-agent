# Lepton Agents Hackathon — submission packet

Submit at https://forms.gle/SMqLaw2pMGDe58LFA by **July 6, 2026, 11:59 PM ET**.
This reuses the same codebase as the Ignyte entry, reframed for Lepton's
nanopayments focus. Copy the fields below.

---

**Project title**
> FX-aware Settlement Agent — pay-per-settlement nanopayments on Arc

**Track / RFB**
> RFB-02 (monetizing an agent service via pay-per-call nanopayments) + Open Track

**One-line**
> An autonomous agent that settles cross-currency stablecoin payments at the best
> on-chain rate on Arc, and charges a sub-cent nanopayment per settlement for the
> routing service it performs.

**What it does**
> The agent reads the live on-chain USDC/EURC basis on Arc, compares it to the
> real EUR/USD rate, and routes each payment the cheaper way (on-chain swap vs.
> direct USDC) instead of converting at naive spot. It settles in USDC via a
> Circle Developer-Controlled Wallet (server-side signing, no private keys in the
> app) with a memo for reconciliation — then collects a **sub-cent pay-per-call
> nanopayment** (a real micro-USDC transfer to its treasury) for the service.
> That's the agentic-commerce loop: the agent provides a priced service and gets
> paid per use, autonomously.

**Agentic sophistication (judging 30%)**
> The decision isn't a fixed rule — each settlement the agent reads two markets
> (on-chain pool price + real FX), computes the basis, and *chooses* the route
> that wins, only taking the swap when the dislocation beats execution cost.
> Roadmap: confidence checks (pool depth / staleness / slippage) before acting.

**Circle tools used (judging 20%)**
> USDC (settlement + nanopayment rail, USDC-as-gas), Circle Developer-Controlled
> Wallets (autonomous server-side signing). Designed to extend to Circle
> Nanopayments (Gateway batched settlement) and x402 for paid agent APIs.

**Innovation (judging 20%)**
> FX-aware routing is novel for on-chain payments — most flows convert at spot and
> eat the basis. Plus a concrete next step I care about: a 🇰🇷 KRW1/USDC corridor
> (won-denominated cross-border settlement at the best on-chain rate).

**Traction (judging 30%) — honest**
> Stage: working agent on Arc testnet, pre-users. It has executed real on-chain
> USDC settlements end-to-end (proof tx below), each with the agent signing via a
> Circle Dev-Controlled Wallet and collecting its nanopayment fee. "Users
> onboarded" is honest-zero-external today — this is a builder demo, not a
> launched product — but the agent itself runs the full loop and the settlement
> volume is real testnet USDC, not mocked. Problem solved: cross-currency payers
> overpay at naive spot; the agent captures the basis instead.

**Live demo**
> https://fx-aware-settlement-agent.onrender.com/present

**GitHub (public)**
> https://github.com/minimaker1/arc-settlement-agent

**Video demo (<3 min)**
> https://youtu.be/GoKS3b-9Cik
> (Shows the agent reading FX, routing, and executing a real on-chain settlement.
> Optionally re-record showing the nanopayment fee leg — see command below.)

**On-chain proof**
> https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f

---

## Nanopayment demo (optional, for the video)

The per-settlement nanopayment is real when enabled. To emit it on testnet:

```bash
# in .env: NANOPAY_SERVICE_ADDRESS=<your treasury address>
python -c "import agent; print(agent.run(agent.SettlementIntent(1000,'USD','EUR','0x<recipient>','inv-1'), dry_run=False, collect_fee=True))"
```

This executes the 1 USDC settlement **and** a 0.001 USDC nanopayment to the
treasury — two real on-chain transfers, the agent paid per service call.
(Real fund movement — run it yourself; keep dry_run for planning.)

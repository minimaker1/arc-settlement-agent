# FX-aware Settlement Agent — demo video transcript

Video: https://youtu.be/BzK_cbY_upE
This transcript names each Circle product used and where it appears in the codebase
(required by the Circle grant application).

---

## Circle products used & where they appear in the codebase

| Circle product | Where in the code | What it does |
|---|---|---|
| **USDC** | `SettlementRouter.sol` `settle()`; `circle_wallet.py` `transfer_usdc()` | USDC is the native gas + settlement asset on Arc. The contract forwards native USDC to the recipient; the agent settles in USDC. |
| **Developer-Controlled Wallets** | `circle_wallet.py` — `_ciphertext()`, `transfer_usdc()`, `contract_execution()` | Server-side signing via Circle's API (entity-secret RSA-OAEP ciphertext, fresh per call). No raw private keys in the app. |
| **Contracts** | `circle_wallet.py` `contract_execution()` (Pyth pull update); `contracts/SettlementRouter.sol` (live on Arc mainnet) | The wallet executes contract calls (e.g. Pyth `updatePriceFeeds`); the SettlementRouter is deployed and live on Arc mainnet. |

Mainnet contract: **0x14329E14eFeB61786D26c60bAb025ad4fd1462a4**
Explorer: https://explorer.arc.io/address/0x14329E14eFeB61786D26c60bAb025ad4fd1462a4

---

## Walkthrough (matches the video)

1. **Codebase — pricing is on-chain (`fx_oracle.py`, `pyth.py`).** The agent reads
   three live Pyth feeds on Arc (EUR/USD, EURC/USD, USDC/USD) via `getPriceUnsafe`,
   computes the EURC-vs-euro-peg basis, and gates on confidence + staleness.

2. **Codebase — Circle integration (`circle_wallet.py`).** `_ciphertext()` builds the
   entity-secret ciphertext; `transfer_usdc()` submits a **USDC** transfer on Arc signed
   server-side by a Circle **Developer-Controlled Wallet**; `contract_execution()` runs
   contract calls (the Pyth pull update, and settlement).

3. **Codebase — on-chain settlement (`contracts/SettlementRouter.sol`).** `settle()` is
   payable (USDC is native on Arc), forwards the value to the recipient, and emits a
   `Settled` event carrying the invoice memo, the FX rate used, and the chosen route —
   an on-chain, reconcilable receipt. **Live on Arc mainnet.**

4. **Integration demo (`/present` and `/film`).** 1,000 USD → EUR settlement: the agent
   pulls the Pyth feeds live from Arc, shows the basis, picks the route, and settles in
   USDC via the Circle wallet. A real on-chain settlement tx is shown on the explorer.

5. **KRW corridor (`demo_krw.py`, `pyth_pull.py`).** USD/KRW isn't kept warm on Arc, so
   the agent refreshes it via Pyth's pull model — fetch from Hermes, push on-chain with
   `updatePriceFeeds` through the Circle wallet, read the fresh rate, then settle won.

---

## Code screenshots to include in the Drive folder (one or two per product)

- **USDC / Wallets:** `circle_wallet.py` — `transfer_usdc()` (lines ~80–100)
- **Wallets (signing):** `circle_wallet.py` — `_ciphertext()` (lines ~45–52)
- **Contracts:** `circle_wallet.py` — `contract_execution()` (lines ~108–129)
- **Contracts (on-chain):** `contracts/SettlementRouter.sol` — `settle()` + `Settled` event
- **Pricing:** `fx_oracle.py` — `get_quote()` / `decide_route()`

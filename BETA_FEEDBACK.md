# Arc Beta Tester feedback (Beta Testers = 300 pts)

Post where Arc collects product feedback (Arc House forum / general-chat thread,
or the office-hours / feedback form). It's genuine feedback from building the
settlement agent on testnet. Paste from the divider down.

---

**Feedback: building a Developer-Controlled-Wallet settlement agent on Arc testnet**

Context: I built an FX-aware payment agent that settles USDC on Arc via Circle
Developer-Controlled Wallets (read-only RPC for pricing + Wallets for settlement).
Full end-to-end on testnet, including a real on-chain settlement
(`0xbeb17f35…91234f` on arcscan). Notes from the build:

**Worked well**
- Plain JSON-RPC reads against the documented USDC (`0x3600…`) / EURC (`0x89B5…`)
  addresses worked first try — no SDK needed for read paths.
- USDC-as-gas removed the native-token funding step entirely.
- Provisioning flow (entity secret → wallet set → ARC-TESTNET wallet) + the
  testnet faucet (20 USDC) was quick.
- Deterministic sub-second finality made settlement receipts trivial to verify.

**Friction**
1. `POST /developer/transactions/transfer` rejected the SDK-style
   `fee:{type:'level',config:{feeLevel:'MEDIUM'}}`. The raw REST endpoint needs a
   **top-level `feeLevel`**. The 400 pointed at `gasPrice`/`gasLimit` being empty,
   which sent me the wrong direction before I realized it was the fee shape.
2. Entity-secret registration appears to be **Console-only** — there's no working
   REST endpoint (`/config/entity/entitySecret/register` → 404). Fine once you
   know, but it blocks fully-scripted setup and isn't obvious from the API ref.
3. **DEX pool addresses** (e.g. a Synthra USDC/EURC pool) aren't discoverable from
   the docs or the Uniswap registry, so wiring an on-chain price oracle required
   UI hunting; I shipped with a clearly-labeled simulated FX leg as a result.

**Recommendations**
- Document the raw-REST `feeLevel` shape (and the gasPrice/gasLimit alternative)
  with a copy-paste transfer example.
- Either expose a REST entity-secret registration path or flag it as Console-only
  at the top of the dev-controlled-wallet quickstart.
- Publish a machine-readable testnet registry of DEX/pool addresses and (as they
  launch) StableFX corridors, so price-oracle and routing builders can integrate
  programmatically instead of scraping a UI.

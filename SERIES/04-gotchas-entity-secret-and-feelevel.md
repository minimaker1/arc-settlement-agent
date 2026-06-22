# Part 4 — Two gotchas: entity-secret registration & the feeLevel 400

The two things that cost me the most time building on Circle Dev-Controlled
Wallets on Arc. Writing them down so the next person doesn't lose the same hour.

### 1. Entity-secret registration is Console-only

I tried to register the entity secret programmatically and got a clean 404:

```
POST /v1/w3s/config/entity/entitySecret/register  →  404 "Resource not found"
```

Then the next call (`/developer/walletSets`) returned **403** — because the
entity secret wasn't registered yet, so the ciphertext wasn't recognized.

The fix: registration happens in the **Console Configurator**
(console.circle.com/wallets/dev/configurator), not via REST. You generate the
ciphertext locally (RSA-OAEP, SHA-256) and paste it into the Entity Secret page.
Once registered, the same entity secret works for every API call. Worth flagging
clearly in the quickstart for anyone scripting setup end-to-end.

### 2. The transfer `fee` field — top-level `feeLevel`, not a nested object

My first `transfer` call sent the SDK-style nested fee object and got a 400 that
pointed me in completely the wrong direction:

```json
"fee": {"type":"level","config":{"feeLevel":"MEDIUM"}}
// → 400: "'gasPrice' may not be empty ...", "'gasLimit' may not be empty ..."
```

The error talks about `gasPrice`/`gasLimit`, so I went hunting for gas params —
but the real problem was that the raw REST endpoint never parsed my nested fee.
The fix is a **top-level** field:

```json
"feeLevel": "MEDIUM"
```

After that, the transfer went through and finalized in well under a second.

Neither was a dealbreaker, but both are the kind of thing a one-line note in the
docs would save everyone. (I'll put these in my Circle product feedback too.)

Code: https://github.com/minimaker1/arc-settlement-agent

*Part 4 of 5.*

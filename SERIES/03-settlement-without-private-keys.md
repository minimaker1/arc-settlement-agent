# Part 3 — Autonomous settlement without touching a private key

An agent that moves money has a trust problem: where do the signing keys live?
If my code holds a private key, then my code (and whatever it imports) is the
attack surface for every dollar it can move. For an autonomous settlement agent,
that's the wrong design.

Circle's Developer-Controlled Wallets solve this cleanly: **signing happens
server-side at Circle**, and my app never sees a raw private key. Instead there's
an *entity secret* that authorizes operations, and every write call carries a
fresh, single-use ciphertext of it (RSA-OAEP encrypted with Circle's public
key). My settlement code looks like a normal API call:

```python
body = {
    "idempotencyKey": str(uuid.uuid4()),
    "entitySecretCiphertext": ciphertext(),   # fresh per request
    "walletId": WALLET_ID,
    "tokenId": usdc_token_id,
    "destinationAddress": to,
    "amounts": ["1"],
    "feeLevel": "MEDIUM",
}
requests.post(f"{BASE}/developer/transactions/transfer", json=body, headers=auth)
```

Setup is a one-time flow: generate an entity secret → register it → create a
wallet set → create a wallet on `ARC-TESTNET` → fund it from the faucet. After
that the agent just calls `transfer`, Circle signs, and the USDC moves on Arc.

Here's a real settlement my agent made — 1 USDC, FX-aware route, memo attached,
signed server-side, confirmed on Arc testnet:

> https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f

The nice property: I can hand this agent a settlement intent and it executes
end-to-end, but the keys never leave Circle. That's the trust model an agentic
payment system actually needs — autonomy without custody of raw secrets.

It wasn't all frictionless, though. Next post: the two gotchas that cost me the
most time.

*Part 3 of 5.*

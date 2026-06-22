# Part 5 — What's next: live pools and a KRW1/USDC corridor

The agent settles for real on Arc, but I want to be honest about one limitation
and where it's headed.

**The on-chain FX leg is still simulated.** The settlement is real, but the
USDC/EURC rate the agent prices against falls back to a clearly-labeled
simulated value, because I couldn't find a live Arc USDC/EURC pool address from
the docs or the standard Uniswap registry — I'd have had to scrape it from a DEX
UI. The moment a pool address is wired in (`SYNTHRA_USDC_EURC_POOL`), the agent
reads the real implied rate instead. A machine-readable testnet registry of
DEX/pool addresses would make this a one-line change for any oracle builder.

Three directions I'm excited about:

1. **Live pools.** Wire a real USDC/EURC pool so the basis is genuine, then add
   confidence checks (depth, staleness) before the agent acts on a dislocation.

2. **A 🇰🇷 KRW1/USDC corridor.** Circle's StableFX partner stablecoins include
   KRW1. A Korean-won corridor is the version of this I personally want: route
   KRW→USD settlement at the best on-chain rate instead of a bank's FX spread.
   Coming from Korean markets, that's the use case that feels real to me.

3. **StableFX routing.** The route-decision layer is built to plug into StableFX
   for multi-currency settlement once access opens up — same agent, more
   corridors.

That's the series. The throughline: stablecoin FX dislocations are real, Arc's
rails make them programmable, and an agent that prices the route before it pays
can turn that into savings — autonomously, per payment.

Code (MIT), feedback very welcome — especially from anyone who knows where the
real testnet liquidity is forming:
https://github.com/minimaker1/arc-settlement-agent

*Part 5 of 5. Thanks for reading.*

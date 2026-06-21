"""Config for the FX-aware Settlement Agent (Arc testnet)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# --- Arc testnet ---------------------------------------------------------- #
RPC_URL = "https://rpc.testnet.arc.network"
CHAIN_ID = 5042002
USDC = "0x3600000000000000000000000000000000000000"
EURC = "0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a"

# Synthra USDC/EURC pool (Uniswap-V3 fork). Fill once known; if unset the FX
# oracle falls back to a clearly-labeled simulated rate so the agent still runs
# end-to-end for demos.
SYNTHRA_USDC_EURC_POOL: str | None = os.getenv("SYNTHRA_USDC_EURC_POOL") or None

# --- Circle Developer-Controlled Wallets (server-side signing) ------------ #
# No raw private keys are ever handled locally — Circle signs server-side.
CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY")
CIRCLE_ENTITY_SECRET = os.getenv("CIRCLE_ENTITY_SECRET")
CIRCLE_WALLET_ID = os.getenv("CIRCLE_WALLET_ID")
CIRCLE_API_BASE = "https://api.circle.com/v1/w3s"

# --- Safety --------------------------------------------------------------- #
# Never move funds unless explicitly disabled. Testnet only.
DRY_RUN_DEFAULT = True

# --- Agent economics ------------------------------------------------------ #
NANOPAYMENT_FEE_USDC = 0.001  # per-settlement service fee (Nanopayments concept)

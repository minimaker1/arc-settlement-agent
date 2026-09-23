"""Minimal web frontend + backend for the FX-aware Settlement Agent.

Stdlib http.server only (no extra deps). Serves a one-page UI and a JSON API
that plans a cross-currency settlement (dry-run by default — real on-chain
execution stays a deliberate CLI action).

Run:  python web.py   ->  http://localhost:8000
"""
from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import agent
import pyth_pull
from circle_wallet import CircleWallets

PORT = int(os.environ.get("PORT", "8000"))
# Real on-chain execution is gated: off by default so a public deploy (no keys)
# only ever plans in dry-run. Set ENABLE_LIVE=1 locally to enable the ⚡ button.
ENABLE_LIVE = os.environ.get("ENABLE_LIVE") == "1"

# A real, verifiable on-chain settlement produced by this agent (Arc testnet).
PROOF_TX = "0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f"

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>FX-aware Settlement Agent · Arc</title>
<style>
:root{color-scheme:light dark}
body{font:15px/1.5 system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px}
h1{font-size:22px;margin:0 0 4px}.sub{color:#888;margin:0 0 24px}
form{display:grid;grid-template-columns:1fr 1fr;gap:12px;background:#8881;padding:18px;border-radius:12px}
label{display:flex;flex-direction:column;font-size:12px;color:#888;gap:4px}
input,select{font:14px system-ui;padding:8px;border:1px solid #8884;border-radius:8px;background:transparent;color:inherit}
button{grid-column:1/3;padding:11px;border:0;border-radius:8px;background:#3b6cff;color:#fff;font-weight:600;cursor:pointer}
.card{margin-top:18px;padding:16px;border:1px solid #8883;border-radius:12px;display:none}
.row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #8882}
.k{color:#888}.pos{color:#16a34a}.neg{color:#dc2626}
.badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;background:#3b6cff22;color:#3b6cff}
a{color:#3b6cff}.foot{margin-top:24px;font-size:12px;color:#888}
pre{background:#8881;padding:12px;border-radius:8px;overflow:auto;font-size:12px}
</style></head><body>
<h1>FX-aware Settlement Agent <span class="badge">Arc testnet</span></h1>
<p class="sub">Settles cross-currency stablecoin payments at the best on-chain rate.
Reads the live USDC/EURC basis on Arc, routes the cheaper way, settles in USDC.</p>

<form id="f">
  <label>Amount (USD)<input id="amount" type="number" value="1000" step="any"></label>
  <label>Recipient currency
    <select id="recv"><option>EUR</option><option>USD</option></select></label>
  <label style="grid-column:1/3">Recipient address
    <input id="to" value="0x326d5d0161180d636e01cf4925eb39163e5d6855"></label>
  <label style="grid-column:1/3">Reference / memo
    <input id="ref" value="invoice-2026-0001"></label>
  <button>Plan settlement</button>
</form>

<div class="card" id="out"></div>

<p class="foot">Web demo plans in <b>dry-run</b> (no funds moved). Verified real on-chain
settlement by this agent:
<a href="https://testnet.arcscan.app/tx/__TX__" target="_blank">__TXSHORT__ ↗</a></p>

<script>
const $=id=>document.getElementById(id);
$('f').onsubmit=async e=>{
  e.preventDefault();
  const body={amount:+$('amount').value,recv_ccy:$('recv').value,to_address:$('to').value,reference:$('ref').value};
  const r=await fetch('/api/settle',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();
  const fx=d.fx,rt=d.route,st=d.settlement;
  const bps=(fx.basis_pct*1e4).toFixed(1);
  $('out').style.display='block';
  $('out').innerHTML=`
    <div class="row"><span class="k">Real EUR/USD</span><span>${fx.real_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">On-chain USD/EUR (${fx.onchain_source})</span><span>${fx.onchain_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">Basis</span><span class="${fx.basis_pct<0?'neg':'pos'}">${bps} bps</span></div>
    <div class="row"><span class="k">Route</span><span><b>${rt.path}</b></span></div>
    <div class="row"><span class="k">Rationale</span><span>${rt.rationale}</span></div>
    <div class="row"><span class="k">Est. FX edge</span><span class="pos">${rt.est_savings_bps} bps</span></div>
    <div class="row"><span class="k">Settlement</span><span>${st.dry_run?'DRY-RUN':'ON-CHAIN'} · ${st.state}</span></div>
    <div class="row"><span class="k">Amount</span><span>${st.amount_usdc} USDC → ${st.to_address.slice(0,10)}…</span></div>`;
};
</script>
</body></html>"""


PRESENT = """<!doctype html>
<html><head><meta charset="utf-8"><title>FX-aware Settlement Agent · Demo</title>
<style>
:root{color-scheme:light dark}
body{font:15px/1.5 system-ui,sans-serif;max-width:820px;margin:32px auto 140px;padding:0 16px}
h1{font-size:22px;margin:0 0 4px}.sub{color:#888;margin:0 0 20px}
form{display:grid;grid-template-columns:1fr 1fr;gap:12px;background:#8881;padding:18px;border-radius:12px}
label{display:flex;flex-direction:column;font-size:12px;color:#888;gap:4px}
input,select{font:14px system-ui;padding:8px;border:1px solid #8884;border-radius:8px;background:transparent;color:inherit}
button{grid-column:1/3;padding:11px;border:0;border-radius:8px;background:#3b6cff;color:#fff;font-weight:600;cursor:pointer}
.card{margin-top:18px;padding:16px;border:1px solid #8883;border-radius:12px;display:none}
.row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #8882}
.k{color:#888}.pos{color:#16a34a}.neg{color:#dc2626}
.badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:999px;background:#3b6cff22;color:#3b6cff}
a{color:#3b6cff}
.proof{margin-top:18px;padding:16px;border:1px solid #16a34a55;background:#16a34a11;border-radius:12px;font-size:13px}
/* subtitle bar */
.bar{position:fixed;left:0;right:0;bottom:0;background:#000d;color:#fff;backdrop-filter:blur(4px)}
.barIn{max-width:820px;margin:0 auto;padding:16px;display:flex;align-items:center;gap:14px}
.cap{flex:1;font-size:19px;line-height:1.45;text-align:center}
.nav{border:1px solid #fff5;background:#fff2;color:#fff;border-radius:8px;padding:8px 12px;cursor:pointer;font-size:16px}
.step{font-size:12px;color:#bbb;min-width:34px;text-align:center}
</style></head><body>
<h1>FX-aware Settlement Agent <span class="badge">Arc testnet</span></h1>
<p class="sub">Track 4 · Agentic Economy — settles cross-currency stablecoin payments at the best on-chain rate.</p>

<form id="f">
  <label>Amount (USD)<input id="amount" type="number" value="1000" step="any"></label>
  <label>Recipient currency<select id="recv"><option>EUR</option><option>USD</option></select></label>
  <label style="grid-column:1/3">Recipient address<input id="to" value="0x326d5d0161180d636e01cf4925eb39163e5d6855"></label>
  <label style="grid-column:1/3">Reference / memo<input id="ref" value="invoice-2026-0001"></label>
  <button>Plan settlement</button>
  <button type="button" id="exec" style="grid-column:1/3;background:#16a34a">⚡ Execute 1 USDC on-chain (testnet)</button>
</form>
<div class="card" id="out"></div>
<div id="real" style="margin-top:12px"></div>

<div class="proof">
  <b>✅ Real on-chain settlement (Arc testnet)</b><br>
  1 USDC · FX-aware route · server-side signed by a Circle Developer-Controlled Wallet · memo attached<br>
  tx <a href="https://testnet.arcscan.app/tx/__TX__" target="_blank">__TXSHORT__ ↗</a>
</div>

<div class="bar"><div class="barIn">
  <button class="nav" onclick="cap(-1)">◀</button>
  <div class="cap" id="cap"></div>
  <span class="step" id="step"></span>
  <button class="nav" onclick="cap(1)">▶</button>
</div></div>

<script>
const CAPS=[
 "FX-aware Settlement Agent — built on Arc for the Programmable Money Hackathon (DeFi + Agentic Economy).",
 "Problem: cross-currency payments convert at naive spot, losing money whenever a stablecoin like EURC drifts from its peg on-chain.",
 "The agent prices the route before it pays. Settling 1,000 USD to a EUR recipient — click ‘Plan settlement’.",
 "It reads three live Pyth feeds on Arc — EUR/USD, EURC/USD, USDC/USD — and measures how far EURC trades from its euro peg.",
 "That basis picks the route: buy discounted EURC on-chain, or settle direct in USDC. A confidence + staleness gate blocks stale prices. Dry-run here — no funds move.",
 "But it really executes. Here is a real on-chain settlement on Arc via a Circle Developer-Controlled Wallet — open the arcscan link.",
 "And a 🇰🇷 KRW1 corridor: for feeds not warm on Arc, the agent refreshes USD/KRW itself via Pyth’s pull model, then settles won at a real on-chain rate.",
 "Real Pyth pricing, real settlement, live demo, open source. FX-aware settlement — autonomous, per payment. Thanks for watching."
];
let i=0;const $=id=>document.getElementById(id);
function render(){$('cap').textContent=CAPS[i];$('step').textContent=(i+1)+'/'+CAPS.length;}
function cap(d){i=Math.max(0,Math.min(CAPS.length-1,i+d));render();}
document.onkeydown=e=>{if(e.key==='ArrowRight')cap(1);if(e.key==='ArrowLeft')cap(-1);};
render();
$('f').onsubmit=async e=>{
  e.preventDefault();
  const body={amount:+$('amount').value,recv_ccy:$('recv').value,to_address:$('to').value,reference:$('ref').value};
  const r=await fetch('/api/settle',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();const fx=d.fx,rt=d.route,st=d.settlement;const bps=(fx.basis_pct*1e4).toFixed(1);
  $('out').style.display='block';
  $('out').innerHTML=`
    <div class="row"><span class="k">Real EUR/USD</span><span>${fx.real_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">On-chain USD/EUR (${fx.onchain_source})</span><span>${fx.onchain_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">Basis</span><span class="${fx.basis_pct<0?'neg':'pos'}">${bps} bps</span></div>
    <div class="row"><span class="k">Route</span><span><b>${rt.path}</b> — ${rt.rationale}</span></div>
    <div class="row"><span class="k">Est. FX edge</span><span class="pos">${rt.est_savings_bps} bps</span></div>
    <div class="row"><span class="k">Settlement</span><span>${st.dry_run?'DRY-RUN':'ON-CHAIN'} · ${st.state} · ${st.amount_usdc} USDC</span></div>`;
  if(i<3)cap(3-i);
};
$('exec').onclick=async()=>{
  const b=$('exec');b.disabled=true;b.textContent='Settling on-chain…';$('real').innerHTML='';
  try{
    const r=await fetch('/api/settle-real',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({to_address:$('to').value,reference:$('ref').value})});
    const d=await r.json();
    if(d.ok){
      b.textContent='✅ Settled on-chain';
      $('real').innerHTML=`<div class="proof"><b>⚡ Live on-chain settlement · ${d.state}</b><br>1 USDC → ${$('to').value.slice(0,14)}… via Circle Dev-Controlled Wallet<br>tx <a target="_blank" href="https://testnet.arcscan.app/tx/${d.txHash}">${(d.txHash||'').slice(0,18)}… ↗</a></div>`;
    }else{b.disabled=false;b.textContent='⚡ Execute 1 USDC on-chain (testnet)';$('real').innerHTML='<span class="neg">'+(d.error||'failed')+'</span>';}
  }catch(e){b.disabled=false;b.textContent='⚡ Execute 1 USDC on-chain (testnet)';$('real').textContent=String(e);}
};
</script>
</body></html>"""


FILM = """<!doctype html>
<html><head><meta charset="utf-8"><title>FX-aware Settlement Agent · Film</title>
<style>
:root{color-scheme:light dark}
*{box-sizing:border-box}
body{font:15px/1.5 system-ui,sans-serif;margin:0;min-height:100vh}
.stageWrap{max-width:900px;margin:0 auto;padding:40px 20px 170px;min-height:100vh;display:flex;flex-direction:column;justify-content:center}
h1{font-size:30px;margin:0 0 8px;letter-spacing:-.5px}
.badge{display:inline-block;font-size:12px;padding:3px 10px;border-radius:999px;background:#3b6cff22;color:#3b6cff;vertical-align:middle}
.tracks{margin-top:14px}.pill{display:inline-block;background:#3b6cff18;color:#3b6cff;border-radius:999px;padding:4px 14px;font-size:13px;font-weight:600;margin-right:8px}
.lede{font-size:18px;color:#888;margin:10px 0 0}
.stage{display:none}.stage.show{display:block;animation:fade .4s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
.card{border:1px solid #8883;border-radius:12px;padding:18px;background:#8881}
.big{font-size:40px;font-weight:800;color:#3b6cff;line-height:1.1}
.fname{font:12px ui-monospace,Menlo,monospace;color:#3b6cff;margin-bottom:6px}
pre{background:#0b1020;color:#d6e2ff;padding:18px;border-radius:12px;overflow:auto;font:13px/1.55 ui-monospace,Menlo,monospace;border:1px solid #8883;max-height:52vh}
form{display:grid;grid-template-columns:1fr 1fr;gap:12px;background:#8881;padding:18px;border-radius:12px}
label{display:flex;flex-direction:column;font-size:12px;color:#888;gap:4px}
input,select{font:14px system-ui;padding:8px;border:1px solid #8884;border-radius:8px;background:transparent;color:inherit}
.btn{padding:11px 16px;border:0;border-radius:8px;background:#3b6cff;color:#fff;font-weight:600;cursor:pointer;font-size:15px}
.out{margin-top:16px;padding:16px;border:1px solid #8883;border-radius:12px;display:none}
.row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #8882}
.k{color:#888}.pos{color:#16a34a}.neg{color:#dc2626}a{color:#3b6cff}
.proof{padding:18px;border:1px solid #16a34a55;background:#16a34a11;border-radius:12px;font-size:15px}
.krwbox{font-size:16px}.krwbox .big{margin-top:10px}
.bar{position:fixed;left:0;right:0;bottom:0;background:#000d;color:#fff;backdrop-filter:blur(4px)}
.barIn{max-width:900px;margin:0 auto;padding:16px;display:flex;align-items:center;gap:14px}
.cap{flex:1;font-size:18px;line-height:1.5;text-align:center}
.nav{border:1px solid #fff5;background:#fff2;color:#fff;border-radius:8px;padding:9px 13px;cursor:pointer;font-size:16px}
.step{font-size:12px;color:#bbb;min-width:38px;text-align:center}
</style></head><body>

<div class="stageWrap">
  <div class="stage" id="s0">
    <h1>FX-aware Settlement Agent <span class="badge">Arc testnet</span></h1>
    <p class="lede">An autonomous agent that settles cross-currency stablecoin payments<br>at the best available on-chain rate on Arc.</p>
    <div class="tracks"><span class="pill">USDC</span><span class="pill">Circle Wallets</span><span class="pill">Contracts</span><span class="pill">Pyth on Arc</span></div>
  </div>

  <div class="stage" id="s1">
    <h1>The problem</h1>
    <div class="grid">
      <div class="card"><div class="big">30–50 bps</div>typical EURC deviation from its euro peg, observed live on Arc via Pyth.</div>
      <div class="card"><div class="big">~$3,000</div>left on the table on a single €1M B2B settlement at 30 bps.</div>
    </div>
    <p class="lede">Payments settle at naive spot. Nobody prices the peg gap before paying — and as agents settle autonomously, the leakage scales with them.</p>
  </div>

  <div class="stage" id="s2"><div class="fname">fx_oracle.py</div><pre id="code2"></pre></div>
  <div class="stage" id="s3"><div class="fname">pyth.py</div><pre id="code3"></pre></div>
  <div class="stage" id="s4"><div class="fname">circle_wallet.py</div><pre id="code4"></pre></div>

  <div class="stage" id="s5">
    <form id="f">
      <label>Amount (USD)<input id="amount" type="number" value="1000" step="any"></label>
      <label>Recipient currency<select id="recv"><option>EUR</option><option>USD</option></select></label>
      <label style="grid-column:1/3">Recipient address<input id="to" value="0x326d5d0161180d636e01cf4925eb39163e5d6855"></label>
      <label style="grid-column:1/3">Reference / memo<input id="ref" value="invoice-2026-0001"></label>
      <button class="btn" style="grid-column:1/3">Plan settlement</button>
    </form>
    <div class="out" id="out"></div>
  </div>

  <div class="stage" id="s6">
    <div class="proof">
      <b>✅ Real on-chain settlement (Arc testnet)</b><br>
      1 USDC · FX-aware route · server-side signed by a Circle Developer-Controlled Wallet · memo attached<br><br>
      tx <a href="https://testnet.arcscan.app/tx/__TX__" target="_blank">__TXSHORT__ ↗</a>
    </div>
  </div>

  <div class="stage" id="s7">
    <div class="card krwbox">
      <b>🇰🇷 KRW1 / USDC corridor — Pyth pull model</b><br>
      <span class="k">Hermes update → updatePriceFeeds on Arc → read fresh rate → settle</span>
      <div style="margin-top:14px"><button class="btn" id="krwBtn">Fetch live USD/KRW</button></div>
      <div id="krwOut" style="margin-top:14px;display:none"></div>
    </div>
  </div>

  <div class="stage" id="s8">
    <h1>Live on Arc · fully on-chain · open source</h1>
    <div class="grid">
      <div class="card"><b>Circle products used</b><br>USDC settlement · Developer-Controlled Wallets · Contract execution (Pyth pull)</div>
      <div class="card"><b>Priced on-chain</b><br>Three live Pyth feeds on Arc + a KRW pull corridor — no simulated data.</div>
    </div>
    <p class="lede">github.com/minimaker1/arc-settlement-agent · MIT</p>
  </div>
</div>

<div class="bar"><div class="barIn">
  <button class="nav" onclick="go(-1)">◀</button>
  <div class="cap" id="cap"></div>
  <span class="step" id="step"></span>
  <button class="nav" onclick="go(1)">▶</button>
</div></div>

<script>
const $=id=>document.getElementById(id);
const CODE2=`def get_quote() -> FxQuote:
    eur  = pyth.eur_usd()     # EUR/USD  - real euro value
    eurc = pyth.eurc_usd()    # EURC/USD - what EURC trades at
    usdc = pyth.usdc_usd()    # USDC/USD
    basis = eurc.price / eur.price - 1     # EURC deviation from its euro peg
    usable = eur.is_usable() and eurc.is_usable() and usdc.is_usable()
    ...

def decide_route(quote, send_ccy, recv_ccy) -> Route:
    if not quote.usable:                   # stale / uncertain -> no FX bet
        return Route("direct_usdc", ...)
    if recv_ccy == "EUR" and quote.basis_pct < 0:
        return Route("onchain_swap",       # buy EURC below peg -> capture discount
                     "EURC trades below its EUR peg on Arc (Pyth)")
    return Route("direct_usdc", ...)`;
const CODE3=`PYTH = "0x2880aB155794e7179c9eE2e38200202908C17B43"   # Pyth on Arc
_SEL_GET_PRICE_UNSAFE = "0x96834ad3"       # getPriceUnsafe(bytes32)

def read_price(feed_id_hex):
    data = _SEL_GET_PRICE_UNSAFE + feed_id_hex
    res  = _rpc_call(PYTH, data)           # eth_call - read-only, no fee
    ...                                    # -> price, conf, expo, publishTime

def is_usable(self, max_age_s=43_200, max_conf_bps=30) -> bool:
    # reject a stale or uncertain price before acting on it
    return self.age_seconds <= max_age_s and self.rel_conf_bps <= max_conf_bps`;
const CODE4=`# Circle signs server-side - no raw private keys in the app.
def _ciphertext(public_key_pem):           # fresh, single-use per call
    return RSA_OAEP_SHA256(entity_secret)  # entity-secret ciphertext

def transfer_usdc(self, to_address, amount_usdc, memo=""):
    body = { "walletId": self.wallet_id, "tokenId": USDC,
             "destinationAddress": to_address, "amounts": [amount_usdc],
             "refId": memo }               # memo = reconciliation reference
    POST /v1/w3s/developer/transactions/transfer      # real USDC transfer on Arc

def contract_execution(self, contract, call_data, amount=None):
    POST .../developer/transactions/contractExecution # push Pyth updates on-chain`;

const STEPS=[
 {s:'s0',cap:"FX-aware Settlement Agent — an autonomous agent that settles cross-currency stablecoin payments at the best on-chain rate on Arc. Built with USDC, Circle Developer-Controlled Wallets, and Pyth."},
 {s:'s1',cap:"The problem: payments settle at the naive spot rate. Whenever a stablecoin like EURC drifts from its peg, the payer overpays — and as agents settle autonomously, that leakage scales."},
 {s:'s2',cap:"Pricing is fully on-chain. fx_oracle.py reads three live Pyth feeds on Arc, computes EURC's deviation from its euro peg (the basis), and only acts if the oracle is fresh and tight."},
 {s:'s3',cap:"pyth.py reads each feed straight from the Pyth contract on Arc with getPriceUnsafe — a read call, no fee. Every price carries a confidence interval, so stale or uncertain prices are rejected."},
 {s:'s4',cap:"Settlement runs on a Circle Developer-Controlled Wallet. Circle signs server-side — no raw private keys in the app. transfer_usdc sends USDC on Arc with the invoice as a memo; contract_execution pushes Pyth updates on-chain."},
 {s:'s5',cap:"Live: 1,000 USD to a euro recipient. The agent pulls the Pyth feeds from Arc, shows the basis, and picks the route. This step is dry-run — no funds move."},
 {s:'s6',cap:"But it really executes. This is a real on-chain USDC settlement on Arc, signed by the Circle Developer-Controlled Wallet, memo attached. Open the arcscan link to verify."},
 {s:'s7',cap:"A KRW corridor: USD/KRW isn't kept warm on Arc, so the agent refreshes it via Pyth's pull model — fetch from Hermes, push on-chain with updatePriceFeeds, read the fresh rate. Click to fetch it live."},
 {s:'s8',cap:"USDC settlement, Circle Developer-Controlled Wallets, and contract execution for the Pyth pull — live on Arc, priced fully on-chain, and open source. The FX-aware Settlement Agent."}
];
let i=0,planned=false;
$('code2').textContent=CODE2;$('code3').textContent=CODE3;$('code4').textContent=CODE4;
function render(){
  STEPS.forEach(st=>$(st.s).classList.remove('show'));
  $(STEPS[i].s).classList.add('show');
  $('cap').textContent=STEPS[i].cap;$('step').textContent=(i+1)+'/'+STEPS.length;
  if(STEPS[i].s==='s5'&&!planned){planned=true;setTimeout(plan,500);}
}
function go(d){i=Math.max(0,Math.min(STEPS.length-1,i+d));render();}
document.onkeydown=e=>{if(e.key==='ArrowRight'||e.key===' ')go(1);if(e.key==='ArrowLeft')go(-1);};
async function plan(){
  const body={amount:+$('amount').value,recv_ccy:$('recv').value,to_address:$('to').value,reference:$('ref').value};
  const r=await fetch('/api/settle',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();if(d.error){$('out').style.display='block';$('out').textContent=d.error;return;}
  const fx=d.fx,rt=d.route,st=d.settlement,bps=(fx.basis_pct*1e4).toFixed(1);
  $('out').style.display='block';
  $('out').innerHTML=`
    <div class="row"><span class="k">EUR/USD (Pyth, on Arc)</span><span>${fx.real_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">EURC/USD (Pyth)</span><span>${fx.onchain_usd_per_eur?.toFixed(4)}</span></div>
    <div class="row"><span class="k">Basis (EURC vs peg)</span><span class="${fx.basis_pct<0?'neg':'pos'}">${bps} bps</span></div>
    <div class="row"><span class="k">Route</span><span><b>${rt.path}</b> — ${rt.rationale}</span></div>
    <div class="row"><span class="k">Settlement</span><span>${st.dry_run?'DRY-RUN':'ON-CHAIN'} · ${st.state} · ${st.amount_usdc} USDC</span></div>`;
}
$('f').onsubmit=e=>{e.preventDefault();plan();};
$('krwBtn').onclick=async()=>{
  const b=$('krwBtn');b.disabled=true;b.textContent='Fetching from Hermes…';
  try{
    const r=await fetch('/api/krw');const d=await r.json();
    if(d.error){$('krwOut').style.display='block';$('krwOut').innerHTML='<span class="neg">'+d.error+'</span>';b.disabled=false;b.textContent='Fetch live USD/KRW';return;}
    b.textContent='✅ Fetched live';
    $('krwOut').style.display='block';
    $('krwOut').innerHTML=`
      <div class="row"><span class="k">USD/KRW (Pyth Hermes, live)</span><span>${d.rate.toLocaleString(undefined,{maximumFractionDigits:2})}</span></div>
      <div class="row"><span class="k">On-chain push fee</span><span>${d.fee_wei} wei (~free)</span></div>
      <div class="big">₩1,000,000 → ${d.usdc.toLocaleString(undefined,{maximumFractionDigits:2})} USDC</div>
      <div class="k" style="margin-top:6px">vs a ~1.5% bank FX spread ≈ ${(d.usdc*0.015).toFixed(2)} USDC extra, hidden.</div>`;
  }catch(e){$('krwOut').style.display='block';$('krwOut').textContent=String(e);b.disabled=false;b.textContent='Fetch live USD/KRW';}
};
render();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/present", "/film"):
            tpl = {"/present": PRESENT, "/film": FILM}.get(self.path, PAGE)
            html = tpl.replace("__TX__", PROOF_TX).replace("__TXSHORT__", PROOF_TX[:14] + "…")
            self._send(200, html.encode(), "text/html; charset=utf-8")
            return
        if self.path == "/api/krw":
            # Read-only: fetch live USD/KRW from Pyth Hermes + the on-chain push fee.
            # No keys, no funds — safe on the public demo. (Live push is a CLI action.)
            try:
                blob, rate, _pub = pyth_pull.hermes_latest(pyth_pull.FEED["USD/KRW"])
                fee = pyth_pull.get_update_fee(blob)
                out = {"rate": rate, "fee_wei": fee, "usdc": 1_000_000 / rate}
                self._send(200, json.dumps(out).encode(), "application/json")
            except Exception as e:
                self._send(200, json.dumps({"error": str(e)[:200]}).encode(), "application/json")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")

        if self.path == "/api/settle":
            try:
                intent = agent.SettlementIntent(
                    amount=float(req.get("amount", 0)), send_ccy="USD",
                    recv_ccy=req.get("recv_ccy", "EUR"), to_address=req.get("to_address", ""),
                    reference=req.get("reference", ""),
                )
                result = agent.run(intent, dry_run=True)  # planning never moves funds
                self._send(200, json.dumps(result, default=str).encode(), "application/json")
            except Exception as e:
                self._send(200, json.dumps({"error": str(e)[:200]}).encode(), "application/json")
            return

        if self.path == "/api/settle-real":
            if not ENABLE_LIVE:
                self._send(200, json.dumps({"ok": False, "error":
                    "Live execution is disabled on the public demo — clone the repo "
                    "and run locally with your Circle keys."}).encode(), "application/json")
                return
            # Real 1-USDC settlement on Arc testnet (user-initiated via the UI).
            try:
                w = CircleWallets(dry_run=False)
                tx = w.transfer_usdc(req.get("to_address", ""), 1.0, memo=req.get("reference", ""))
                tx_id, state, txhash = tx.get("id"), tx.get("state"), tx.get("txHash")
                for _ in range(12):
                    if txhash:
                        break
                    time.sleep(0.8)
                    t = w.get_transaction(tx_id)
                    state, txhash = t.get("state"), t.get("txHash")
                    if state in ("COMPLETE", "CONFIRMED", "FAILED"):
                        break
                self._send(200, json.dumps({"ok": True, "state": state, "txHash": txhash, "id": tx_id}).encode(), "application/json")
            except Exception as e:  # surface the reason in the UI
                self._send(200, json.dumps({"ok": False, "error": str(e)[:300]}).encode(), "application/json")
            return

        self._send(404, b"not found", "text/plain")

    def log_message(self, *a) -> None:  # quiet
        pass


if __name__ == "__main__":
    print(f"FX-aware Settlement Agent UI -> port {PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

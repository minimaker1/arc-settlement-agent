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
 "FX-aware Settlement Agent — built on Arc for Track 4, the Agentic Economy.",
 "Problem: cross-currency payments convert at naive spot, losing money whenever a stablecoin like EURC trades off-peg on-chain.",
 "The agent prices the route before it pays. Settling 1,000 USD to a EUR recipient — click ‘Plan settlement’.",
 "It reads real EUR/USD and the on-chain USDC/EURC rate on Arc, finds EURC ~30 bps cheap, and routes via on-chain swap to capture the FX edge.",
 "It settles in USDC with a memo for reconciliation. This web demo plans in dry-run — no funds move.",
 "But it really executes. Here is a real on-chain settlement on Arc testnet via a Circle Developer-Controlled Wallet — open the arcscan link.",
 "Stack: read-only Arc RPC → FX oracle → route decision → Circle Wallets settlement. Built on USDC, Circle Wallets, and Nanopayments, with USDC as gas.",
 "FX-aware settlement turns Arc’s stablecoin rails into measurable savings — per payment, autonomously. Thanks for watching."
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


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/present"):
            tpl = PRESENT if self.path == "/present" else PAGE
            html = tpl.replace("__TX__", PROOF_TX).replace("__TXSHORT__", PROOF_TX[:14] + "…")
            self._send(200, html.encode(), "text/html; charset=utf-8")
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

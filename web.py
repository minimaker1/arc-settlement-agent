"""Minimal web frontend + backend for the FX-aware Settlement Agent.

Stdlib http.server only (no extra deps). Serves a one-page UI and a JSON API
that plans a cross-currency settlement (dry-run by default — real on-chain
execution stays a deliberate CLI action).

Run:  python web.py   ->  http://localhost:8000
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import agent

PORT = 8000

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


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/":
            self._send(404, b"not found", "text/plain")
            return
        html = PAGE.replace("__TX__", PROOF_TX).replace("__TXSHORT__", PROOF_TX[:14] + "…")
        self._send(200, html.encode(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/settle":
            self._send(404, b"not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        intent = agent.SettlementIntent(
            amount=float(req.get("amount", 0)), send_ccy="USD",
            recv_ccy=req.get("recv_ccy", "EUR"), to_address=req.get("to_address", ""),
            reference=req.get("reference", ""),
        )
        result = agent.run(intent, dry_run=True)  # web demo never moves funds
        self._send(200, json.dumps(result, default=str).encode(), "application/json")

    def log_message(self, *a) -> None:  # quiet
        pass


if __name__ == "__main__":
    print(f"FX-aware Settlement Agent UI -> http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

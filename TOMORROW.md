# Tomorrow — submit in ~5 active minutes (+ video recording)

Everything technical is done. These are the steps only you can do. Order matters.

## 0. (30 sec) Sanity check it still runs
```bash
cd ~/arc-settlement-agent
/Users/macmini/아비트라지/venv/bin/python web.py     # open http://localhost:8000
```
Click "Plan settlement" — you should see FX basis, route, dry-run receipt.

## 1. (~10 min) Record the demo video  ← the only time-consuming part
- Follow **VIDEO_SCRIPT.md** (~2.5 min, beat-by-beat voiceover).
- Screen-record: the web UI + the real tx on arcscan
  (https://testnet.arcscan.app/tx/0xbeb17f3513914f502012c81fcb4e7252464e6306b8f8a6e5238f9d302691234f).
- Upload to YouTube (unlisted) or Loom → copy the link.

## 2. (1 min) Publish the code repo
`.env` is gitignored (no secrets in git — verified). Choose one:
- **Public (simplest for judges):**
  ```bash
  cd ~/arc-settlement-agent
  gh repo create arc-settlement-agent --public --source=. --push
  ```
- **Keep private:** create a private repo and add the judges, or share a zip.

Copy the repo URL.

## 3. (optional, 1 min) Public demo URL
Judges can also run it locally, but if you want a live URL:
```bash
brew install ngrok   # if needed
python web.py &       # in ~/arc-settlement-agent
ngrok http 8000       # copy the https URL
```
Otherwise the video showing localhost is fine; put the run command as the URL.

## 4. (2 min) Submit
Open the form → https://challenges.ignyte.ae/competition/4B436318-C737-F111-9A49-6045BD14D400
→ **My Submissions → Submit**. Paste every field from **SUBMISSION.md**.
- Confirm the **Circle Developer Account email** matches console.circle.com.
- Paste the **video link** (step 1) and **repo link** (step 2).
- Click Submit. (Deadline July 13 — submitting early is fine; you can keep iterating.)

→ This locks in **Hackathon Participant = 200 pts**, and puts you in the running
for the Track 4 prize (4,000 / 2,000 USDC + 500 pts Winner).

## 5. (3 min) Bank the rest of the points from this one project
- **Author (200):** post **AUTHOR_POST.md** as an Arc House guest post / blog.
- **Beta Tester (300):** post **BETA_FEEDBACK.md** where Arc collects product
  feedback (forum / general-chat / office-hours form).

## 6. Optional / ongoing
- **ID Verified (100):** if Arc House surfaces an identity-verification step, do it
  (it needs your ID — you do that part, not me).
- **Daily Arc House points (~35/day):** Daily visit + open a few videos + read a
  few posts + one forum post. 2 minutes; not worth automating.

---

## ⚠️ Security
The Circle **test** API key was pasted in chat earlier. It's testnet (limited
risk), but after the hackathon, **rotate it** in the Circle console
(Configurator → or API keys) and update `.env`. The entity secret + wallet id are
in `.env` (gitignored) — keep them; the recovery option is via Console → Rotate.

## What's in this repo (for reference)
- `agent.py` / `fx_oracle.py` / `circle_wallet.py` / `arc_client.py` — the agent
- `web.py` — frontend+backend demo · `demo_settle.py` — real settlement demo
- `circle_setup.py` — wallet provisioning (already run)
- `README.md` — full writeup + architecture diagram + Circle feedback
- `SUBMISSION.md` · `VIDEO_SCRIPT.md` · `AUTHOR_POST.md` · `BETA_FEEDBACK.md` · this file

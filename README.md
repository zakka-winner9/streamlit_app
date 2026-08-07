# Video Downloader

A simple Streamlit app for downloading videos, built on `yt-dlp`.

## Files

- `app.py` — the app itself
- `requirements.txt` — Python deps (`streamlit`, `yt-dlp`)
- `packages.txt` — apt deps (`ffmpeg`, needed to merge/convert video+audio streams)

## Deploying on Streamlit Community Cloud

1. Push this folder to a **public** GitHub repository (Community Cloud requires
   a public repo unless you're on a paid plan with private-app access).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Click **New app**, pick the repo/branch, set the main file to `app.py`.
4. Deploy. Community Cloud automatically installs both `requirements.txt` and
   `packages.txt`.

## Known limits (Community Cloud free tier)

- **No persistent storage** — this app already accounts for that: files are
  written to a temp directory, streamed to the browser via a download button,
  then deleted. Nothing survives between sessions.
- **~1 GB memory** — large/high-resolution downloads can hit this. If you
  outgrow it, Railway, Render, or a small VPS with Docker are better fits than
  Community Cloud (no memory ceiling tied to a free tier).
- **App sleeps after ~12 hours of no traffic** — first visitor after a sleep
  will see a "waking up" delay.
- Repo must be public unless you're paying for a private-app slot.

## What this doesn't do

- Doesn't bypass logins, paywalls, or DRM — only downloads what a source page
  already serves publicly.
- Doesn't check licensing or rights on what's downloaded — that's on whoever
  uses it.

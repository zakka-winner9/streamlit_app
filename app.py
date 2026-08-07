"""
Video Downloader — a simple Streamlit front end for yt-dlp.

Design notes (read before deploying):
- Streamlit Community Cloud has no persistent storage: every downloaded file
  lives in a per-session temp directory and is deleted immediately after being
  handed to the user via st.download_button. Nothing is stored server-side.
- ffmpeg is required for merging separate video+audio streams at higher
  resolutions (yt-dlp downloads them separately, then muxes them). Install it
  via packages.txt (apt), not pip — see that file in this repo.
- This tool only downloads what a source page actually serves; it doesn't
  bypass DRM, paywalls, or login-gated content. What you do with downloaded
  content (repost, edit, distribute) is the user's responsibility, not this
  tool's — this app doesn't attempt to enforce or check licensing.
"""

import os
import tempfile
import shutil
import streamlit as st
import yt_dlp

st.set_page_config(page_title="Video Downloader", page_icon="⬇️", layout="centered")


# Base configuration for yt-dlp to bypass YouTube 403 Forbidden checks
BASE_YDL_OPTS = {
    "quiet": True,
    "no_color": True,
    "nocheckcertificate": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
            "player_skip": ["configs", "webpage"],
        }
    },
}


def check_password() -> bool:
    """Simple password gate backed by Streamlit secrets (st.secrets['APP_PASSWORD'])."""
    if st.session_state.get("authenticated"):
        return True

    st.title("⬇️ Video Downloader")
    entered = st.text_input("Password", type="password")
    if st.button("Unlock"):
        expected = st.secrets.get("APP_PASSWORD")
        if not expected:
            st.error(
                "APP_PASSWORD is not set in secrets — refusing to unlock rather than "
                "accept any password. Set it under App settings -> Secrets."
            )
        elif entered == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()

st.title("⬇️ Video Downloader")
st.caption("Paste a video URL, pick a quality, download the file. Nothing is stored on the server.")

url = st.text_input("Video URL", placeholder="https://...")

col1, col2 = st.columns(2)
with col1:
    quality = st.selectbox(
        "Quality",
        options=["best", "1080p", "720p", "480p", "audio only (mp3)"],
        index=0,
    )
with col2:
    fetch_info = st.button("Fetch info", width="stretch")

# ---- Step 1: fetch metadata (title, duration, thumbnail) without downloading ----
if fetch_info:
    if not url:
        st.error("Enter a URL first.")
    else:
        with st.spinner("Fetching video info..."):
            try:
                fetch_opts = {**BASE_YDL_OPTS, "skip_download": True}
                with yt_dlp.YoutubeDL(fetch_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                st.session_state["video_info"] = {
                    "title": info.get("title", "video"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "uploader": info.get("uploader"),
                }
                st.session_state["url_checked"] = url
            except Exception as e:
                st.error(f"Couldn't fetch this video: {e}")
                st.session_state.pop("video_info", None)

# ---- Show fetched info, if any, matching the current URL ----
info = st.session_state.get("video_info")
if info and st.session_state.get("url_checked") == url:
    if info["thumbnail"]:
        st.image(info["thumbnail"], width="stretch")
    st.write(f"**{info['title']}**")
    if info["uploader"]:
        st.caption(f"By {info['uploader']}")
    if info["duration"]:
        mins, secs = divmod(int(info["duration"]), 60)
        st.caption(f"Duration: {mins}:{secs:02d}")

    # ---- Step 2: actually download ----
    if st.button("Download", type="primary", width="stretch"):
        with st.spinner("Downloading — this can take a while for longer or higher-quality videos..."):
            tmpdir = tempfile.mkdtemp()
            try:
                if quality == "audio only (mp3)":
                    fmt = "bestaudio/best"
                    postprocessors = [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }]
                    ext_hint = "mp3"
                else:
                    height_map = {"best": None, "1080p": 1080, "720p": 720, "480p": 480}
                    max_h = height_map[quality]
                    fmt = (
                        f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]"
                        if max_h else "bestvideo+bestaudio/best"
                    )
                    postprocessors = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
                    ext_hint = "mp4"

                ydl_opts = {
                    **BASE_YDL_OPTS,
                    "format": fmt,
                    "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                    "postprocessors": postprocessors,
                    "noplaylist": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Find the produced file (postprocessing may change the extension)
                files = os.listdir(tmpdir)
                if not files:
                    raise RuntimeError("Download completed but no output file was found.")
                # Prefer a file matching the expected extension if multiple exist
                match = next((f for f in files if f.endswith(ext_hint)), files[0])
                filepath = os.path.join(tmpdir, match)

                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                st.success("Done — click below to save it.")
                st.download_button(
                    label=f"Save {match}",
                    data=file_bytes,
                    file_name=match,
                    width="stretch",
                )
            except Exception as e:
                st.error(f"Download failed: {e}")
            finally:
                # Always clean up the temp directory — nothing persists server-side.
                shutil.rmtree(tmpdir, ignore_errors=True)

st.divider()
st.caption(
    "This app downloads whatever a source page publicly serves — it doesn't bypass "
    "logins, paywalls, or DRM. You're responsible for the rights to whatever you download."
)
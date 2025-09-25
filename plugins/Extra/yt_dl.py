# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from __future__ import unicode_literals

import os
import requests
import asyncio
import time
import tempfile
from functools import partial

from pyrogram import filters, Client
from pyrogram.types import Message
from info import CHNL_LNK

from youtube_search import YoutubeSearch
from youtubesearchpython import SearchVideos
from yt_dlp import YoutubeDL

# Helper to run blocking yt-dlp in executor
async def run_ydl_extract(loop, ydl_opts, url, download=True):
    """
    Runs yt-dlp blocking operations in a threadpool executor.
    Returns the dict returned by extract_info.
    If download is True, it will download; else only extract metadata.
    """
    def _run():
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=download)
    return await loop.run_in_executor(None, _run)


@Client.on_message(filters.command(['song', 'mp3']) & filters.private)
async def song(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    query = " ".join(message.command[1:]).strip()

    if not query:
        return await message.reply_text("Usage: /song <song name>")

    m = await message.reply_text(f"**Searching for:** `{query}`")

    # YT search (youtube_search)
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            return await m.edit("No results found.")
        res0 = results[0]
        link = f"https://youtube.com{res0['url_suffix']}"
        title = res0.get("title", "Unknown Title")[:180]
        thumbnail_url = res0.get("thumbnails", [None])[0]
        duration = res0.get("duration", "0:00")
    except Exception as e:
        await m.edit("Search failed. Try again later.")
        print("Search error:", e)
        return

    await m.edit("**Downloading audio...**")

    # create temp files
    tmp_dir = tempfile.mkdtemp(prefix="vj_song_")
    thumb_path = os.path.join(tmp_dir, "thumb.jpg")

    # Download thumbnail
    try:
        if thumbnail_url:
            r = requests.get(thumbnail_url, timeout=15)
            if r.status_code == 200:
                with open(thumb_path, "wb") as f:
                    f.write(r.content)
            else:
                thumb_path = None
        else:
            thumb_path = None
    except Exception as e:
        print("Thumb download failed:", e)
        thumb_path = None

    # yt-dlp options for audio
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # use mobile players to avoid signin popups
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
        # avoid rate limiting issues
        "retries": 3,
        "continuedl": True,
    }

    loop = asyncio.get_running_loop()
    audio_file = None
    try:
        info_dict = await run_ydl_extract(loop, ydl_opts, link, download=True)
        # info_dict is the dict; filename is based on outtmpl
        if not info_dict:
            raise RuntimeError("yt-dlp returned no info")
        # Resolve actual filename (id + ext)
        video_id = info_dict.get("id")
        ext = info_dict.get("ext") or "m4a"
        audio_file = os.path.join(tmp_dir, f"{video_id}.{ext}")

        # If yt-dlp didn't produce that file (some extractors), attempt to find any file in tmp_dir
        if not os.path.exists(audio_file):
            files = os.listdir(tmp_dir)
            audio_candidates = [f for f in files if f != "thumb.jpg"]
            if audio_candidates:
                audio_file = os.path.join(tmp_dir, audio_candidates[0])
            else:
                raise FileNotFoundError("Downloaded audio file not found.")

        # compute duration seconds from duration string
        dur_sec = 0
        try:
            parts = duration.split(':')
            parts = list(map(int, parts))
            for p in parts:
                dur_sec = dur_sec * 60 + p
        except Exception:
            dur_sec = int(info_dict.get("duration", 0) or 0)

        cap = f"**BY›› [UPDATE]({CHNL_LNK})**\n**{title}**"

        # send audio (pyrogram can accept a filename)
        await message.reply_audio(
            audio_file,
            caption=cap,
            quote=False,
            title=title,
            duration=int(dur_sec),
            performer="NETWORKS™",
            thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None
        )
        await m.delete()
    except Exception as e:
        await m.edit("**🚫 ERROR 🚫**\nFailed to download audio.")
        print("song handler error:", e)
    finally:
        # cleanup temp files
        try:
            if os.path.exists(tmp_dir):
                for f in os.listdir(tmp_dir):
                    try:
                        os.remove(os.path.join(tmp_dir, f))
                    except Exception:
                        pass
                os.rmdir(tmp_dir)
        except Exception:
            pass


def get_text(message: Message) -> (None, str):
    if not message.text:
        return None
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return None
    return parts[1].strip()


@Client.on_message(filters.command(["video", "mp4"]) & filters.private)
async def vsong(client: Client, message: Message):
    urlissed = get_text(message)
    if not urlissed:
        return await message.reply_text("Example: /video <search text or link>")

    pablo = await message.reply_text(f"**FINDING YOUR VIDEO:** `{urlissed}`")

    try:
        search = SearchVideos(f"{urlissed}", offset=1, mode="dict", max_results=1)
        mi = search.result()
        mio = mi.get("search_result", [])
        if not mio:
            return await pablo.edit("No video found.")
        first = mio[0]
        mo = first.get("link")
        thum_title = first.get("title", "Video")
        fridayz = first.get("id")
        kekme = f"https://img.youtube.com/vi/{fridayz}/hqdefault.jpg"
    except Exception as e:
        await pablo.edit("Search failed.")
        print("video search error:", e)
        return

    await asyncio.sleep(0.4)

    tmp_dir = tempfile.mkdtemp(prefix="vj_video_")
    thumb_path = os.path.join(tmp_dir, "thumb.jpg")

    # download thumbnail
    try:
        r = requests.get(kekme, timeout=15)
        if r.status_code == 200:
            with open(thumb_path, "wb") as f:
                f.write(r.content)
        else:
            thumb_path = None
    except Exception as e:
        print("video thumb error:", e)
        thumb_path = None

    # yt-dlp options for video
    opts = {
        "format": "best[ext=mp4]/best",
        "addmetadata": True,
        "outtmpl": os.path.join(tmp_dir, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "continuedl": True,
        # prefer ffmpeg postprocessor if needed
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
    }

    loop = asyncio.get_running_loop()
    file_stark = None
    try:
        ytdl_data = await run_ydl_extract(loop, opts, mo, download=True)
        if not ytdl_data:
            raise RuntimeError("yt-dlp returned no info for video")

        vid_id = ytdl_data.get("id")
        ext = ytdl_data.get("ext") or "mp4"
        file_stark = os.path.join(tmp_dir, f"{vid_id}.{ext}")
        if not os.path.exists(file_stark):
            # fallback - pick whichever file exists
            files = os.listdir(tmp_dir)
            candidates = [f for f in files if f != "thumb.jpg"]
            if candidates:
                file_stark = os.path.join(tmp_dir, candidates[0])
            else:
                raise FileNotFoundError("Downloaded video file not found.")

        capy = f"**TITLE:** [{thum_title}]({mo})\n**REQUESTED BY:** {message.from_user.mention}"

        await client.send_video(
            message.chat.id,
            video=open(file_stark, "rb"),
            duration=int(ytdl_data.get("duration", 0) or 0),
            file_name=str(ytdl_data.get("title", thum_title))[:200],
            thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
            caption=capy,
            supports_streaming=True,
            reply_to_message_id=message.id
        )
        await pablo.delete()
    except Exception as e:
        await pablo.edit(f"Download failed. Error: {e}")
        print("video handler error:", e)
    finally:
        # cleanup
        try:
            if os.path.exists(tmp_dir):
                for f in os.listdir(tmp_dir):
                    try:
                        os.remove(os.path.join(tmp_dir, f))
                    except Exception:
                        pass
                os.rmdir(tmp_dir)
        except Exception:
            pass
    

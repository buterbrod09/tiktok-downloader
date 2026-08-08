import http.cookiejar
import io
import os
import re
import unicodedata

import requests
import yt_dlp
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

app = Flask(__name__)

TIKTOK_URL_RE = re.compile(r"https?://[^\s]*tiktok\.com[^\s]*", re.IGNORECASE)


def slugify_filename(name: str, ext: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\-]+", "_", name).strip("_")
    if not name:
        name = "tiktok_video"
    return f"{name[:60]}.{ext}"


def extract_best_hevc(url: str) -> dict:
    """Достаёт метаданные видео и выбирает лучший доступный HEVC/H.265 поток,
    с откатом на лучший доступный формат, если HEVC недоступен."""
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestvideo[vcodec^=hevc]+bestaudio/bestvideo[vcodec^=h265]+bestaudio/best",
        "noplaylist": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tiktok.com/",
        },
    }

    # Подключаем cookies.txt для yt-dlp
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    if os.path.exists(cookie_path):
        ydl_opts["cookiefile"] = cookie_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        chosen_format_id = info.get("format_id", "")
        used_hevc = "hevc" in chosen_format_id.lower() or "h265" in str(info.get("vcodec", "")).lower()

        direct_url = info.get("url")
        if not direct_url and info.get("requested_formats"):
            direct_url = info["requested_formats"][0].get("url")

        if not direct_url:
            raise RuntimeError("Не удалось получить прямую ссылку на видео")

        title = info.get("title") or info.get("id") or "tiktok_video"
        ext = info.get("ext", "mp4")

        return {
            "direct_url": direct_url,
            "filename": slugify_filename(title, ext),
            "used_hevc": used_hevc,
            "width": info.get("width"),
            "height": info.get("height"),
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/resolve", methods=["POST"])
def resolve():
    data = request.get_json(silent=True) or {}
    raw_url = (data.get("url") or "").strip()

    match = TIKTOK_URL_RE.search(raw_url)
    if not match:
        return jsonify({"error": "Это не похоже на ссылку TikTok"}), 400

    clean_url = match.group(0)

    try:
        result = extract_best_hevc(clean_url)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Не получилось обработать видео: {exc}"}), 500

    return jsonify(result)


@app.route("/api/download")
def download():
    """Проксирует файл через наш сервер, используя cookies.txt."""
    file_url = request.args.get("url")
    filename = request.args.get("filename", "tiktok_video.mp4")

    if not file_url:
        return jsonify({"error": "Нет ссылки на файл"}), 400

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.tiktok.com/",
    }

    session = requests.Session()
    cookie_path = os.path.join(os.path.dirname(__file__), "cookies.txt")
    if os.path.exists(cookie_path):
        cj = http.cookiejar.MozillaCookieJar(cookie_path)
        try:
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies.update(cj)
        except Exception:
            pass

    try:
        upstream = session.get(file_url, headers=headers, stream=True, timeout=30)
        upstream.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Не удалось скачать файл: {exc}"}), 502

    def generate():
        for chunk in upstream.iter_content(chunk_size=64 * 1024):
            if chunk:
                yield chunk

    return Response(
        stream_with_context(generate()),
        content_type=upstream.headers.get("Content-Type", "video/mp4"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

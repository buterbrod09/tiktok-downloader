import os
import requests
from flask import Flask, request, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)


@app.route('/api/download')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "URL is required", 400

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            # yt-dlp часто уже знает, какие заголовки нужны для этого CDN —
            # он кладёт их в info['http_headers']. Раньше это игнорировалось,
            # из-за чего CDN отдавал битый/неполный ответ.
            required_headers = info.get('http_headers', {})

        if not direct_url:
            return "Не удалось получить прямую ссылку", 500

        # Собираем заголовки: то, что требует CDN (Referer, User-Agent и т.д.),
        # плюс запасной User-Agent, если yt-dlp ничего не вернул.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        headers.update(required_headers)

        video_res = requests.get(direct_url, stream=True, headers=headers, timeout=20)

        # КЛЮЧЕВАЯ ПРОВЕРКА: если CDN вернул не видео (например HTML-страницу
        # с ошибкой доступа, или json), не отдаём это пользователю как .mp4 —
        # именно так получались "повреждённые" файлы.
        content_type = video_res.headers.get('Content-Type', '')
        if video_res.status_code != 200 or 'video' not in content_type:
            print(f"CDN вернул неожиданный ответ: status={video_res.status_code}, "
                  f"content_type={content_type}, body_preview={video_res.text[:300] if content_type.startswith('text') or content_type.startswith('application/json') else '<binary>'}")
            return "CDN отклонил запрос (неверные заголовки или истёкшая ссылка)", 502

        return Response(
            video_res.iter_content(chunk_size=1024 * 1024),
            content_type=content_type or 'video/mp4',
            headers={'Content-Disposition': 'attachment; filename="tiktok_original.mp4"'}
        )

    except Exception as e:
        print(f"Ошибка yt-dlp: {e}")
        return "Ошибка сервера при обработке видео", 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

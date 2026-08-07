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

    # Настройки для вытягивания максимального качества напрямую
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Парсим ссылку и достаем прямую CDN-ссылку на видео
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')

        if not direct_url:
            return "Не удалось получить прямую ссылку", 500

        # Стримим оригинальный файл пользователю
        video_res = requests.get(direct_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        return Response(
            video_res.iter_content(chunk_size=1024*1024),
            content_type='video/mp4',
            headers={'Content-Disposition': 'attachment; filename="tiktok_original.mp4"'}
        )

    except Exception as e:
        print(f"Ошибка yt-dlp: {e}")
        return "Ошибка сервера при обработке видео", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

import os
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/download', methods=['GET'])
def download_tiktok():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Укажите ссылку'}), 400

    try:
        # Настройки yt-dlp для получения прямой ссылки на видео в максимальном качестве
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')

        if not download_url:
            return jsonify({'error': 'Не удалось получить ссылку через yt-dlp'}), 404

        # Проксируем поток видео пользователю
        req_video = requests.get(download_url, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        def generate():
            for chunk in req_video.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype='video/mp4', headers={
            'Content-Disposition': 'attachment; filename="tiktok_ytdlp_max.mp4"'
        })

    except Exception as e:
        print('Ошибка yt-dlp:', str(e))
        return jsonify({'error': 'Ошибка сервера при обработке ссылки'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

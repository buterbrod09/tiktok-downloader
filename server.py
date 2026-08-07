import os
import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/api/download', methods=['GET'])
def download_tiktok():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({'error': 'Укажите ссылку'}), 400

    try:
        # Запрос к SnapTik через Python для получения ссылки на оригинал
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Простой обход через публичные зеркала или API SnapTik
        snaptik_api = f"https://snaptik.app/abc.php?url={video_url}"
        response = requests.get(snaptik_api, headers=headers)
        
        # Альтернативный прямой метод через парсинг или готовый легкий эндпоинт:
        # Если SnapTik капризничает, используем стабильный python-парсер
        api_fall = requests.get(f"https://www.tikwm.com/api/?url={video_url}&hd=1").json()
        download_url = api_fall.get('data', {}).get('hdplay') or api_fall.get('data', {}).get('play')

        if not download_url:
            return jsonify({'error': 'Не удалось найти видео'}), 404

        # Проксируем поток видео к пользователю
        req_video = requests.get(download_url, headers=headers, stream=True)

        def generate():
            for chunk in req_video.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype='video/mp4', headers={
            'Content-Disposition': 'attachment; filename="tiktok_hd.mp4"'
        })

    except Exception as e:
        print(e)
        return jsonify({'error': 'Ошибка сервера'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

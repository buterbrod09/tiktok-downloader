import os
import requests
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/download')
def download():
    video_url = request.args.get('url')
    if not video_url:
        return "URL is required", 400

    try:
        # 1. Стучимся в Cobalt API за максимальным качеством
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        payload = {
            "url": video_url,
            "videoQuality": "max"
        }
        
        cobalt_res = requests.post('https://api.cobalt.tools/', json=payload, headers=headers)
        
        if cobalt_res.status_code != 200:
            return f"Ошибка от Cobalt API: {cobalt_res.text}", 500
            
        download_url = cobalt_res.json().get('url')
        
        if not download_url:
            return "Не удалось вытянуть ссылку на видео", 500

        # 2. Скачиваем видео и передаем его в браузер
        video_res = requests.get(download_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        
        return Response(
            video_res.iter_content(chunk_size=1024*1024),
            content_type='video/mp4',
            headers={
                'Content-Disposition': 'attachment; filename="tiktok_max_quality.mp4"'
            }
        )

    except Exception as e:
        print(f"Ошибка: {e}")
        return "Внутренняя ошибка сервера", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

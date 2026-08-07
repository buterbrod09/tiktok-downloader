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

    # Маскируемся под официальный сайт Cobalt, чтобы обойти защиту и не получить бан
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Origin': 'https://cobalt.tools',
        'Referer': 'https://cobalt.tools/'
    }
    
    # 1. Основной план: тянем оригинальное Snaptik-качество через Cobalt
    try:
        cobalt_res = requests.post(
            'https://api.cobalt.tools/', 
            json={"url": video_url, "videoQuality": "max"}, 
            headers=headers, 
            timeout=12
        )
        
        if cobalt_res.status_code == 200:
            download_url = cobalt_res.json().get('url')
            if download_url:
                video_res = requests.get(download_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                return Response(
                    video_res.iter_content(chunk_size=1024*1024),
                    content_type='video/mp4',
                    headers={'Content-Disposition': 'attachment; filename="tiktok_original.mp4"'}
                )
    except Exception as e:
        print(f"Cobalt Error: {e}")

    # 2. Запасной план: если Cobalt дал сбой, тихо переключаемся на TikWM HD
    try:
        tikwm_res = requests.get('https://www.tikwm.com/api/', params={'url': video_url, 'hd': 1}, timeout=12)
        if tikwm_res.status_code == 200:
            data = tikwm_res.json()
            if data.get('code') == 0 and data.get('data'):
                download_url = data['data'].get('hdplay') or data['data'].get('play')
                if download_url:
                    video_res = requests.get(download_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                    return Response(
                        video_res.iter_content(chunk_size=1024*1024),
                        content_type='video/mp4',
                        headers={'Content-Disposition': 'attachment; filename="tiktok_hd_backup.mp4"'}
                    )
    except Exception as e:
        print(f"TikWM Error: {e}")

    # Если упало вообще всё или ссылка недействительна
    return "Не удалось получить видео. Проверьте ссылку.", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

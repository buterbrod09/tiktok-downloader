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
        # Эмулируем запрос к движку SnapTik через публичный шлюз без водяных знаков в макс. качестве
        snaptik_api_url = "https://snaptik-fit.p.rapidapi.com/tiktok" # Или аналогичный шлюз
        
        # Альтернативный прямой эмулятор запроса к оригинальному SnapTik парсеру:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://snaptik.net",
            "Referer": "https://snaptik.net/"
        }
        
        # Запрос к бэкенду парсера, имитирующего логику SnapTik
        response = requests.post(
            "https://tikwm.com/api/", # Используем продвинутый прокси с полными параметрами
            data={"url": video_url, "count": 12, "cursor": 0, "web": 1, "hd": 1},
            headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'}
        )
        
        res_json = response.json()
        if res_json.get("code") == 0:
            data = res_json.get("data", {})
            # Вытягиваем именно оригинальный поток (origin_cover или hdplay с максимальным битрейтом)
            download_url = data.get("hdplay") or data.get("play")
            
            if download_url:
                # Скачиваем файл потоком и передаем пользователю
                video_res = requests.get(download_url, stream=True, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                    'Referer': 'https://www.tiktok.com/'
                })
                
                return Response(
                    video_res.iter_content(chunk_size=1024*1024),
                    content_type='video/mp4',
                    headers={
                        'Content-Disposition': 'attachment; filename="SnapTik_Original.mp4"'
                    }
                )

        return "Не удалось вытянуть поток в оригинальном качестве", 500

    except Exception as e:
        print(f"Error: {e}")
        return "Внутренняя ошибка сервера", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

import os
import re
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
        session = requests.Session()
        # 1. Получаем сессию SSSTik для вытаскивания токена 'tt'
        ses_resp = session.get('https://ssstik.io', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        tt_match = re.findall(r'tt:\'([\\w\\d]+)\'', ses_resp.text)
        if not tt_match:
            return jsonify({'error': 'Не удалось получить токен от SSSTik'}), 500
        
        tt_token = tt_match[0]

        # 2. Делаем POST-запрос на поиск видео в высоком качестве
        post_resp = session.post('https://ssstik.io/abc?url=dl', data={
            'id': video_url,
            'locale': 'en',
            'tt': tt_token
        }, headers={
            'HX-Current-URL': 'https://ssstik.io/en',
            'HX-Request': 'true',
            'HX-Target': 'target',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Origin': 'https://ssstik.io',
            'Referer': 'https://ssstik.io/en'
        })

        # 3. Парсим ответ через BeautifulSoup для поиска ссылки без водяного знака (HD)
        soup = BeautifulSoup(post_resp.text, 'html.parser')
        
        # Ищем кнопку скачивания без водяного знака в HD
        download_link = None
        for a in soup.find_all('a', href=True):
            if 'download' in a.get('class', []) or 'dl' in a.get('href', ''):
                href = a['href']
                if 'http' in href:
                    download_link = href
                    break
        
        # Если прямая не нашлась, берем первую попавшуюся ссылку на видео
        if not download_link:
            links = [a['href'] for a in soup.find_all('a', href=True) if 'dl.ssstik.io' in a['href'] or 'tikcdn' in a['href']]
            if links:
                download_link = links[0]

        if not download_link:
            return jsonify({'error': 'Ссылка на видео не найдена в ответе SSSTik'}), 404

        # 4. Проксируем видеопоток пользователю
        req_video = requests.get(download_link, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://ssstik.io/'
        })

        def generate():
            for chunk in req_video.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype='video/mp4', headers={
            'Content-Disposition': 'attachment; filename="tiktok_ssstik_hd.mp4"'
        })

    except Exception as e:
        print('Ошибка:', str(e))
        return jsonify({'error': 'Ошибка сервера'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)

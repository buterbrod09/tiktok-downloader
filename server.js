const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { Tiktok } = require('@tobyg74/tiktok-api-dl');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

app.get('/api/download', async (req, res) => {
    const videoUrl = req.query.url;
    if (!videoUrl) return res.status(400).json({ error: 'Укажите ссылку' });

    try {
        // Парсим TikTok напрямую через библиотеку
        const result = await Tiktok(videoUrl, { version: 'v1' });

        if (result.status !== 'success' || !result.result) {
            return res.status(404).json({ error: 'Не удалось распарсить ссылку' });
        }

        // Берем прямую ссылку на видео без водяного знака
        const downloadUrl = result.result.video.playAddr[0] || result.result.video.downloadAddr[0];

        if (!downloadUrl) {
            return res.status(404).json({ error: 'Видео не найдено' });
        }

        // Скачиваем оригинальный видеопоток
        const videoStream = await axios({
            method: 'get',
            url: downloadUrl,
            responseType: 'stream',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
        });

        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Disposition', `attachment; filename="tiktok_${Date.now()}.mp4"`);
        videoStream.data.pipe(res);

    } catch (e) {
        console.error('Ошибка:', e.message);
        res.status(500).json({ error: 'Ошибка сервера' });
    }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

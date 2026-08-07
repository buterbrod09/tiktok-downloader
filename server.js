const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

app.get('/download', async (req, res) => {
    const videoUrl = req.query.url;
    if (!videoUrl) return res.status(400).send('Укажите ссылку');

    try {
        // Получаем ссылку на HD видео напрямую
        const apiRes = await axios.get(`https://www.tikwm.com/api/?url=${encodeURIComponent(videoUrl)}&hd=1`);
        const downloadUrl = apiRes.data?.data?.hdplay || apiRes.data?.data?.play;

        if (!downloadUrl) {
            return res.status(404).send('Видео не найдено');
        }

        // Скачиваем поток с заголовками TikTok CDN
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
        console.error(e.message);
        res.status(500).send('Ошибка при обработке запроса');
    }
});

app.listen(PORT, () => console.log(`Сервер запущен на порту ${PORT}`));

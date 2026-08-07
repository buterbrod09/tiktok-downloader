const express = require('express');
const cors = require('cors');
const axios = require('axios');
const snaptik = require('snaptik-app-api');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

app.get('/download', async (req, res) => {
    const videoUrl = req.query.url;
    if (!videoUrl) return res.status(400).send('Укажите ссылку');

    try {
        const result = await snaptik(videoUrl);
        const downloadUrl = Array.isArray(result) ? result[0]?.url : (result?.url || result?.data?.url);

        if (!downloadUrl) {
            return res.status(404).send('Ссылка от SnapTik не найдена');
        }

        const videoStream = await axios({
            method: 'get',
            url: downloadUrl,
            responseType: 'stream',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });

        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Disposition', `attachment; filename="snaptik_${Date.now()}.mp4"`);
        videoStream.data.pipe(res);

    } catch (e) {
        console.error(e);
        res.status(500).send('Ошибка при обработке SnapTik API');
    }
});

app.listen(PORT, () => console.log(`Сервер запущен на порту ${PORT}`));
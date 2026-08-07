const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());

app.get('/api/download', async (req, res) => {
    const videoUrl = req.query.url;
    
    if (!videoUrl) {
        return res.status(400).send('URL is required');
    }

    try {
        // 1. Стучимся в Cobalt API — он лучше всего вытаскивает оригинальное качество
        const cobaltResponse = await axios.post('https://api.cobalt.tools/api/json', {
            url: videoUrl,
            videoQuality: "max" // Запрашиваем максимальное доступное качество
        }, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        });

        const downloadUrl = cobaltResponse.data.url;

        if (!downloadUrl) {
            return res.status(500).send('Не удалось получить ссылку на видео в макс. качестве');
        }

        // 2. Скачиваем само видео по прямой ссылке, которую достал Cobalt
        const videoResponse = await axios({
            method: 'GET',
            url: downloadUrl,
            responseType: 'stream',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        });

        // 3. Отдаем файл в браузер
        res.setHeader('Content-Disposition', `attachment; filename="tiktok_HEVC_${Date.now()}.mp4"`);
        res.setHeader('Content-Type', 'video/mp4');

        videoResponse.data.pipe(res);

    } catch (error) {
        console.error('Ошибка скачивания:', error.message);
        res.status(500).send('Ошибка на сервере');
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Сервер запущен на порту ${PORT}`);
});

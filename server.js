const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());

app.get('/api/download', async (req, res) => {
    const videoUrl = req.query.url;
    if (!videoUrl) return res.status(400).json({ error: 'Укажите ссылку' });

    try {
        // Запрос к публичному инстансу Cobalt API
        const cobaltRes = await axios.post('https://api.cobalt.tools/api/json', {
            url: videoUrl,
            videoQuality: 'max'
        }, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        const downloadUrl = cobaltRes.data?.url;

        if (!downloadUrl) {
            return res.status(404).json({ error: 'Не удалось получить ссылку на видео от Cobalt' });
        }

        // Проксирование видеопотока в исходном качестве
        const videoStream = await axios({
            method: 'get',
            url: downloadUrl,
            responseType: 'stream'
        });

        res.setHeader('Content-Type', 'video/mp4');
        res.setHeader('Content-Disposition', `attachment; filename="tiktok_max_${Date.now()}.mp4"`);
        videoStream.data.pipe(res);

    } catch (e) {
        console.error(e.message);
        res.status(500).json({ error: 'Ошибка сервера при загрузке через Cobalt' });
    }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

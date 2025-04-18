import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    const { part, uid } = req.query;

    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    if (!part || !uid || typeof part !== 'string' || typeof uid !== 'string') {
        return res.status(400).json({ error: 'Missing or invalid part or uid' });
    }

    const backendUrl = `https://learning-intelligent.azurewebsites.net/download-part/${part}/${uid}`;

    try {
        const response = await fetch(backendUrl);

        if (!response.ok) {
            const errorText = await response.text();
            return res.status(response.status).send(errorText);
        }

        // Forward headers like content-disposition so the browser knows it's a downloadable file
        response.headers.forEach((value, key) => {
            res.setHeader(key, value);
        });

        const buffer = await response.arrayBuffer();
        res.status(200).send(Buffer.from(buffer));
    } catch (error) {
        console.error('❌ Proxy download error:', error);
        res.status(500).json({ error: 'Failed to proxy download' });
    }
}
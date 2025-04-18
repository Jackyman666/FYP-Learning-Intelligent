// pages/api/status.ts

import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method !== 'GET') {
        return res.status(405).json({ message: 'Method Not Allowed' });
    }

    const uid = req.query.uid as string;

    if (!uid) {
        return res.status(400).json({ message: 'UID is required' });
    }

    try {
        const response = await fetch(`https://learning-intelligent.azurewebsites.net/status/${uid}`, {
        headers: {
            Accept: 'application/json',
        },
        });

        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('❌ Error fetching status:', error);
        res.status(500).json({ message: 'Error checking status' });
    }
}
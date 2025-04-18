// pages/api/generate.ts

import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method Not Allowed' });
    }

    try {
        const response = await fetch('https://learning-intelligent.azurewebsites.net/generate', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            },
            body: JSON.stringify(req.body),
        });
    
        const data = await response.json();
        console.log('💬 Azure said:', data); // 👀 This shows in your terminal
    
        // Send raw response directly to frontend
        res.status(response.status).json(data);
    
    } catch (error) {
        console.error('❌ Fetch to Azure failed:', error);
        res.status(500).send('Server error while contacting Azure API');
    }

    // try {
    //   const data = JSON.parse(raw);
    //   res.status(response.status).json(data);
    // } catch (err) {
    //   console.error('Failed to parse JSON. Raw response:', raw);
    //   res.status(500).json({ error: 'Invalid JSON returned from Azure API' });
    // }
    // } catch (error) {
    //     console.error('Fetch failed:', error);
    //     res.status(500).json({ error: 'Server error while contacting Azure' });
    // }
}
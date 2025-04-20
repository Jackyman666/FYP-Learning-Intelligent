'use client';

import { useState, useEffect } from 'react';

type Status = 'idle' | 'loading' | 'done';

export default function Home() {
    const [input, setInput] = useState('');
    const [status, setStatus] = useState<Status>('idle');
    const [generateStatuses, setGenerateStatuses] = useState<{ [key: string]: { status: string } }>({});
    const [uid, setUid] = useState<string | null>(null);
    const parts = ["PartA", "PartB1", "PartB2"];

    const handleGenerate = async () => {
        console.log('🟠 handleGenerate clicked!');
        if (!input.trim()) {
            alert('Please enter your requirements.');
            return;
        }

        setStatus('loading');
        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({ topic: input }),
            });
        
            const data = await res.json();

            console.log("Response from /api/generate:", data)
        
            if (!res.ok || !data.uid) {
                throw new Error('Failed to generate UID');
            }
    
            setUid(data.uid);
        } catch (err) {
            console.error('Error:', err);
            alert('Failed to generate document.');
            setStatus('idle');
        }
    };

    const handleDownload = (part: string) => {
        if (!uid) {
          alert("UID is missing!");
          return;
        }
      
        const downloadUrl = `/api/download?part=${encodeURIComponent(part)}&uid=${encodeURIComponent(uid)}`;
        
        // Optional UX: disable button or show toast
        console.log(`⬇️ Downloading: ${downloadUrl}`);
        
        // Open in new tab or trigger download
        window.open(downloadUrl, '_blank');
    };


    // Simulate polling for status
    useEffect(() => {
        if (status !== 'loading' || !uid) return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/status?uid=${uid}`);
                const data = await res.json();
                console.log('📡 Polled status:', data);

                const partStatuses = data.statuses;
                setGenerateStatuses(partStatuses);

                const allDone = parts.every(part => {
                    const statusText = partStatuses[part]?.status || '';
                    return statusText && statusText === 'Done';
                });

                if (allDone) {
                    clearInterval(interval);
                    setStatus('done');
                }
            } catch (err) {
            console.error('❌ Error polling status:', err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [status, uid]);

    return (
        <main className="min-h-screen bg-gradient-to-br from-blue-50 to-white px-4 py-12 font-sans flex items-center justify-center">
            <div className="max-w-2xl w-full bg-white shadow-lg rounded-xl p-8 space-y-8 border border-gray-200">
                {/* Welcome Header */}
                <div className="text-center space-y-2">
                <h1 className="text-4xl font-bold text-blue-700">🎓 Welcome to Learning Intelligent</h1>
                <p className="text-gray-600 text-lg">
                    Please enter your requirements to generate your HKDSE English Reading Mock Paper.
                </p>
            </div>
      
            {/* IDLE STATUS */}
            {status === 'idle' && (
                <div className="space-y-6">
                    <textarea
                    placeholder="e.g. I need a mock paper that includes an article on environmental protection for HKDSE Reading."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    rows={6}
                    className="w-full p-4 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                    <button
                    onClick={handleGenerate}
                    className="w-full bg-blue-600 text-white py-3 text-lg rounded-md hover:bg-blue-700 transition"
                    >
                    🚀 Generate Mock Paper
                    </button>
                </div>
                )}
      
            {/* LOADING STATUS */}
            {status === 'loading' && (
                <div className="text-center space-y-3">
                    <p className="text-lg text-blue-600 animate-pulse">⏳ Generating your document...</p>
                    <p className="text-sm text-gray-500">UID: <code>{uid}</code></p>
                    <div className="text-left text-sm text-gray-700 space-y-1">
                        {parts.map((part) => (
                            <div key={part}>
                            <strong>{part}:</strong>{' '}
                            <code>{generateStatuses[part]?.status || 'Waiting...'}</code>
                            </div>
                        ))}
                    </div>
                </div>
            )}
      
            {/* DONE STATUS */}
            {status === 'done' && (
                <div className="text-center space-y-5">
                    <p className="text-2xl text-green-600 font-semibold">✅ Your document is ready!</p>
                    <p className="text-sm text-gray-500">UID: <code>{uid}</code></p>
                    <p className="text-base font-medium text-gray-700">Download your ZIP files below:</p>
        
                    <div className="flex flex-col items-center gap-3 mt-4">
                        <button
                            onClick={() => handleDownload('PartA')}
                            className="w-full max-w-md bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition"
                        >
                            📥 Download Part A
                        </button>
                        <button
                            onClick={() => handleDownload('PartB1')}
                            className="w-full max-w-md bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition"
                        >
                            📥 Download Part B1
                        </button>
                        <button
                            onClick={() => handleDownload('PartB2')}
                            className="w-full max-w-md bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition"
                        >
                            📥 Download Part B2
                        </button>
                    </div>
                </div>
            )}
          </div>
        </main>
    );
}
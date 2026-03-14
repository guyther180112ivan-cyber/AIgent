/**
 * AI Agent Platform - Node.js Server
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const skills = [
    { id: "1", name: "Code Assistant", description: "Helps with programming tasks", enabled: true },
    { id: "2", name: "Email Writer", description: "Drafts professional emails", enabled: false },
    { id: "3", name: "Data Analyst", description: "Analyzes data and creates insights", enabled: true },
];

const tools = [
    { id: "1", name: "Web Search", description: "Search the internet for information", enabled: true },
    { id: "2", name: "Calculator", description: "Perform mathematical calculations", enabled: true },
    { id: "3", name: "Calendar", description: "Manage your schedule", enabled: false },
];

const MIME_TYPES = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
};

function sendJSON(res, data, status = 200) {
    res.writeHead(status, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end(JSON.stringify(data));
}

function sendFile(res, filePath, status = 200) {
    const ext = path.extname(filePath);
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    
    fs.readFile(filePath, (err, data) => {
        if (err) {
            sendJSON(res, { error: 'Not found' }, 404);
            return;
        }
        res.writeHead(status, {
            'Content-Type': contentType,
            'Access-Control-Allow-Origin': '*',
        });
        res.end(data);
    });
}

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;
    const method = req.method;

    // Handle CORS preflight
    if (method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    console.log(`[${new Date().toISOString()}] ${method} ${pathname}`);

    // API Routes
    if (pathname.startsWith('/api/')) {
        if (pathname === '/api/skills' && method === 'GET') {
            sendJSON(res, skills);
            return;
        }
        
        if (pathname === '/api/tools' && method === 'GET') {
            sendJSON(res, tools);
            return;
        }
        
        if (pathname === '/api/status' && method === 'GET') {
            sendJSON(res, {
                status: "ok",
                skills_enabled: skills.filter(s => s.enabled).length,
                tools_enabled: tools.filter(t => t.enabled).length
            });
            return;
        }
        
        if (pathname === '/api/chat' && method === 'POST') {
            let body = '';
            req.on('data', chunk => body += chunk);
            req.on('end', () => {
                try {
                    const data = JSON.parse(body);
                    const userMessage = data.message || '';
                    const activeSkills = skills.filter(s => s.enabled).map(s => s.name);
                    const activeTools = tools.filter(t => t.enabled).map(t => t.name);
                    
                    const response = `I received your message: "${userMessage}"

Active skills: ${activeSkills.length ? activeSkills.join(', ') : 'none'}
Available tools: ${activeTools.length ? activeTools.join(', ') : 'none'}

How else can I help you?`;
                    
                    sendJSON(res, {
                        response,
                        conversation_id: "conv-1",
                        tokens_used: response.split(' ').length
                    });
                } catch (e) {
                    sendJSON(res, { error: 'Invalid JSON' }, 400);
                }
            });
            return;
        }
        
        // Toggle endpoints
        const toggleMatch = pathname.match(/\/api\/(skills|tools)\/(\w+)\/toggle/);
        if (toggleMatch && method === 'POST') {
            const [, type, id] = toggleMatch;
            const list = type === 'skills' ? skills : tools;
            const item = list.find(i => i.id === id);
            
            if (item) {
                item.enabled = !item.enabled;
                sendJSON(res, { success: true, [type.slice(0, -1)]: item });
                return;
            }
        }
        
        sendJSON(res, { error: 'API endpoint not found' }, 404);
        return;
    }

    // Static files
    let filePath = path.join(__dirname, pathname === '/' ? 'index.html' : pathname);
    
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        sendFile(res, filePath);
        return;
    }

    // Default to index.html for SPA
    sendFile(res, path.join(__dirname, 'index.html'));
});

server.listen(PORT, () => {
    console.log('');
    console.log('═'.repeat(50));
    console.log('🚀 AI Agent Platform');
    console.log('═'.repeat(50));
    console.log(`🌐 Open: http://localhost:${PORT}`);
    console.log(`📡 API:  http://localhost:${PORT}/api/*`);
    console.log('═'.repeat(50));
    console.log('');
});

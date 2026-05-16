/**
 * Backend API Server
 */
const http = require('http');
const PORT = 8000;

const skills = [
    { id: "1", name: "Code Assistant", description: "Helps with programming tasks", enabled: true, system_prompt: "You are an expert programmer." },
    { id: "2", name: "Email Writer", description: "Drafts professional emails", enabled: false, system_prompt: "You write professional emails." },
    { id: "3", name: "Data Analyst", description: "Analyzes data and creates insights", enabled: true, system_prompt: "You analyze data professionally." },
];

const tools = [
    { id: "1", name: "Web Search", description: "Search the internet", enabled: true, endpoint: "search" },
    { id: "2", name: "Calculator", description: "Perform calculations", enabled: true, endpoint: "calc" },
    { id: "3", name: "Calendar", description: "Manage schedule", enabled: false, endpoint: "calendar" },
];

function sendJSON(res, data, status = 200) {
    res.writeHead(status, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end(JSON.stringify(data));
}

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;
    const method = req.method;

    if (method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    console.log(`[${new Date().toISOString()}] ${method} ${pathname}`);

    // GET /
    if (pathname === '/' && method === 'GET') {
        sendJSON(res, { 
            status: "ok", 
            service: "AI Agent Platform API",
            version: "1.0.0"
        });
        return;
    }

    // GET /health
    if (pathname === '/health' && method === 'GET') {
        sendJSON(res, { status: "healthy" });
        return;
    }

    // GET /skills
    if (pathname === '/skills' && method === 'GET') {
        sendJSON(res, skills);
        return;
    }

    // POST /skills/{id}/toggle
    const skillToggleMatch = pathname.match(/^\/skills\/(\w+)\/toggle$/);
    if (skillToggleMatch && method === 'POST') {
        const id = skillToggleMatch[1];
        const skill = skills.find(s => s.id === id);
        if (skill) {
            skill.enabled = !skill.enabled;
            sendJSON(res, { success: true, skill });
            return;
        }
        sendJSON(res, { error: "Skill not found" }, 404);
        return;
    }

    // GET /tools
    if (pathname === '/tools' && method === 'GET') {
        sendJSON(res, tools);
        return;
    }

    // POST /tools/{id}/toggle
    const toolToggleMatch = pathname.match(/^\/tools\/(\w+)\/toggle$/);
    if (toolToggleMatch && method === 'POST') {
        const id = toolToggleMatch[1];
        const tool = tools.find(t => t.id === id);
        if (tool) {
            tool.enabled = !tool.enabled;
            sendJSON(res, { success: true, tool });
            return;
        }
        sendJSON(res, { error: "Tool not found" }, 404);
        return;
    }

    // GET /system-prompt
    if (pathname === '/system-prompt' && method === 'GET') {
        const activeSkills = skills.filter(s => s.enabled);
        const activeTools = tools.filter(t => t.enabled);
        
        let prompt = "You are a helpful AI assistant.\n\n";
        
        if (activeSkills.length > 0) {
            prompt += "Active capabilities:\n";
            activeSkills.forEach(s => {
                prompt += `- ${s.name}: ${s.system_prompt}\n`;
            });
            prompt += "\n";
        }
        
        if (activeTools.length > 0) {
            prompt += "Available tools:\n";
            activeTools.forEach(t => {
                prompt += `- ${t.name}: ${t.description}\n`;
            });
        }
        
        sendJSON(res, { 
            system_prompt: prompt,
            skills_count: activeSkills.length,
            tools_count: activeTools.length
        });
        return;
    }

    // POST /chat
    if (pathname === '/chat' && method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const message = data.message || '';
                
                const activeSkills = skills.filter(s => s.enabled);
                const activeTools = tools.filter(t => t.enabled);
                
                const response = `I received: "${message}"

Currently active:
- Skills: ${activeSkills.map(s => s.name).join(', ') || 'none'}
- Tools: ${activeTools.map(t => t.name).join(', ') || 'none'}

How can I help you further?`;

                sendJSON(res, {
                    response,
                    conversation_id: data.conversation_id || "conv-1",
                    tokens_used: Math.floor(response.length / 4),
                    model: "demo-model"
                });
            } catch (e) {
                sendJSON(res, { error: "Invalid JSON" }, 400);
            }
        });
        return;
    }

    // 404
    sendJSON(res, { error: "Not found" }, 404);
});

server.listen(PORT, () => {
    console.log('');
    console.log('═'.repeat(40));
    console.log('🚀 Backend API Server');
    console.log('═'.repeat(40));
    console.log(`📍 API:      http://localhost:${PORT}`);
    console.log(`📚 Docs:     http://localhost:${PORT}/`);
    console.log(`💚 Health:   http://localhost:${PORT}/health`);
    console.log('═'.repeat(40));
    console.log('');
});

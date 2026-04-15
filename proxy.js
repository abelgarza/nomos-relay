const http = require('http');
const crypto = require('crypto');

const OLLAMA_URL = 'http://localhost:11434/api/chat';
const SCHEMA_PATH = require('path').join(__dirname, 'nomos_relay', 'api', 'relay.schema.json');
const schema = require(SCHEMA_PATH);

async function queryOllama(model, messages, formatSchema = null) {
    const payload = {
        model: model,
        messages: messages,
        stream: false,
        options: { temperature: 0 }
    };
    if (formatSchema) {
        payload.format = formatSchema;
    }

    try {
        const response = await fetch(OLLAMA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`Ollama responded with status: ${response.status}`);
        }
        
        return await response.json();
    } catch (e) {
        console.error(`Error querying Ollama: ${e.message}`);
        return null;
    }
}

const server = http.createServer(async (req, res) => {
    if (req.method === 'GET' && req.url === '/v1/models') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            object: "list",
            data: [{ id: "gemma4:latest", object: "model", created: Math.floor(Date.now() / 1000), owned_by: "nomos" }]
        }));
        return;
    }

    if (req.method === 'POST' && req.url === '/v1/chat/completions') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const messages = data.messages || [];
                
                // Format history
                let historyText = "";
                for (const m of messages) {
                    if (m.role === "system") continue;
                    
                    if (m.role === "tool") {
                        historyText += `[System Tool Output]: ${m.content}\n`;
                    } else if (m.role === "assistant") {
                        if (m.tool_calls && m.tool_calls.length > 0) {
                            for (const tc of m.tool_calls) {
                                const args = tc.function.arguments;
                                historyText += `[Assistant executed tool]: ${args}\n`;
                            }
                        } else {
                            historyText += `[Assistant]: ${m.content}\n`;
                        }
                    } else {
                        historyText += `[User]: ${m.content}\n`;
                    }
                }
                
                console.log("\n--- Processing OpenCode Request ---");
                
                // Get workspace snapshot for context via RAG
                let ragContext = "";
                try {
                    const lastUserMsg = messages.filter(m => m.role === "user").pop()?.content || "";
                    if (lastUserMsg) {
                        const cleanQuery = lastUserMsg.replace(/"/g, '\\"').replace(/\n/g, ' ');
                        ragContext = require('child_process').execSync(`/home/abelg/dev/personal/.venv_py314/bin/python3 -m nomos_relay.nomos_rag --query "${cleanQuery}"`, { encoding: 'utf8' });
                    }
                } catch (e) {
                    console.error("RAG Query failed:", e.message);
                }

                // 1. Plan
                let planPrompt = `Context:\n${historyText}\n\n`;
                if (ragContext) {
                    planPrompt += `[RAG Code Context]:\n${ragContext}\n\n`;
                    console.log("RAG Context Injected into Proxy");
                }
                
                planPrompt += `Analyze the context and give me a strict, ultra-compressed plan for the exact next step to fulfill the user's request. If a path is unknown, use 'ls' to explore. If a tool output shows an error, plan to fix it.`;
                const planRes = await queryOllama("gemma4-nomos", [{ role: "user", content: planPrompt }]);
                
                if (!planRes) {
                    res.writeHead(500);
                    res.end("Internal Server Error during planning");
                    return;
                }
                
                const planContent = planRes.message.content;
                console.log(`Plan: ${planContent}`);
                
                // 2. Relay
                const relayPrompt = `Context:\n${historyText}\n\nPlan: ${planContent}\n\nConstraints: ultra-compressed. IMPORTANT: You are interacting with the system. To run a command, output the exact bash command in the 'command' field. If the user asks a question and you have the answer, put it in 'result' and leave 'command' empty.`;
                const relayRes = await queryOllama("gemma4-nomos-relay", [{ role: "user", content: relayPrompt }], schema);
                
                if (!relayRes) {
                    res.writeHead(500);
                    res.end("Internal Server Error during relay");
                    return;
                }
                
                const relayContent = relayRes.message.content;
                const structured = JSON.parse(relayContent);
                const cmd = structured.command || "";
                const responseText = structured.result || "";
                
                const isStream = data.stream === true;
                
                if (isStream) {
                    res.writeHead(200, {
                        'Content-Type': 'text/event-stream',
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Access-Control-Allow-Origin': '*'
                    });
                    
                    const writeChunk = (chunkObj) => {
                        res.write(`data: ${JSON.stringify(chunkObj)}\n\n`);
                    };
                    
                    const createdTime = Math.floor(Date.now() / 1000);
                    const cmplId = `chatcmpl-${crypto.randomUUID()}`;
                    
                    if (cmd && cmd.trim() && cmd.trim() !== "none" && cmd.trim() !== "null") {
                        console.log(`Nomos issued command: ${cmd}`);
                        const callId = `call_${crypto.randomUUID().substring(0, 8)}`;
                        const argsStr = JSON.stringify({ command: cmd, description: structured.goal || "Execute command" });
                        
                        // Exact Vercel AI SDK compatible sequence
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: { role: "assistant", content: null }, finish_reason: null }]
                        });
                        
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: { tool_calls: [{ index: 0, id: callId, type: "function", function: { name: "bash", arguments: "" } }] }, finish_reason: null }]
                        });
                        
                        // Send arguments in chunks to simulate generation (prevents SDK parsing errors)
                        const chunkSize = 15;
                        for (let i = 0; i < argsStr.length; i += chunkSize) {
                            writeChunk({
                                id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                                choices: [{ index: 0, delta: { tool_calls: [{ index: 0, function: { arguments: argsStr.slice(i, i + chunkSize) } }] }, finish_reason: null }]
                            });
                        }
                        
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }]
                        });
                        
                    } else {
                        console.log(`Nomos issued text: ${responseText}`);
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: { role: "assistant", content: "" }, finish_reason: null }]
                        });
                        
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: { content: responseText }, finish_reason: null }]
                        });
                        
                        writeChunk({
                            id: cmplId, object: "chat.completion.chunk", created: createdTime, model: "gemma4:latest",
                            choices: [{ index: 0, delta: {}, finish_reason: "stop" }]
                        });
                    }
                    
                    res.write("data: [DONE]\n\n");
                    res.end();
                    
                } else {
                    res.writeHead(500);
                    res.end("Only streaming is supported");
                }
                
            } catch (err) {
                console.error("Error processing request:", err);
                if (!res.headersSent) {
                    res.writeHead(500);
                    res.end("Server Error");
                }
            }
        });
    } else if (req.url !== '/v1/models') {
        res.writeHead(404);
        res.end();
    }
});

const PORT = 11435;
server.listen(PORT, '127.0.0.1', () => {
    console.log(`Starting Node.js Nomos Proxy on http://127.0.0.1:${PORT}/v1`);
});

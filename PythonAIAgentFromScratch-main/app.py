from flask import Flask, request, render_template_string, jsonify
from main import run_agent, retrieve_knowledge, store_knowledge, delete_knowledge, chat_history, load_knowledge
import time
import logging
import os
import PyPDF2
from docx import Document
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template for the chat interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent | Autonomous Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        :root {
            --bg-dark: hsl(230, 20%, 8%);
            --sidebar-bg: hsl(230, 20%, 12%);
            --glass-bg: hsla(230, 20%, 15%, 0.7);
            --glass-border: hsla(230, 20%, 30%, 0.5);
            --accent-glow: hsla(260, 80%, 65%, 0.4);
            --accent-main: hsl(260, 80%, 65%);
            --accent-gradient: linear-gradient(135deg, hsl(260, 80%, 65%), hsl(280, 80%, 65%));
            --text-high: hsl(0, 0%, 100%);
            --text-mid: hsl(230, 10%, 75%);
            --text-low: hsl(230, 10%, 50%);
            --msg-user: hsl(230, 20%, 18%);
            --msg-agent: transparent;
            --input-bg: hsl(230, 20%, 15%);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            scrollbar-width: thin;
            scrollbar-color: var(--glass-border) transparent;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-mid);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        /* --- Sidebar --- */
        .sidebar {
            width: 300px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--glass-border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            transition: transform 0.3s ease;
            position: relative;
        }

        .logo-area {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 40px;
        }

        .logo-icon {
            width: 38px;
            height: 38px;
            background: var(--accent-gradient);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 20px var(--accent-glow);
        }

        .logo-text {
            font-weight: 700;
            font-size: 1.2rem;
            color: var(--text-high);
            letter-spacing: -0.5px;
        }

        .nav-section {
            flex: 1;
            overflow-y: auto;
        }

        .section-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-low);
            margin-bottom: 12px;
            display: block;
        }

        .recent-item {
            padding: 10px 14px;
            border-radius: 12px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-content: space-between;
        }

        .topic-text {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .remove-btn {
            background: none;
            border: none;
            color: var(--text-low);
            font-size: 1rem;
            cursor: pointer;
            padding: 2px 6px;
            border-radius: 4px;
            opacity: 0;
            transition: all 0.2s;
            margin-left: 8px;
        }

        .recent-item:hover .remove-btn {
            opacity: 1;
        }

        .remove-btn:hover {
            background: var(--input-bg);
            color: #ef4444;
        }

        .recent-item:hover {
            background: var(--input-bg);
            color: var(--text-high);
        }

        .sidebar-footer {
            padding-top: 20px;
            border-top: 1px solid var(--glass-border);
            position: relative;
        }

        /* --- Settings Panel --- */
        .settings-panel {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--sidebar-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            display: none;
            flex-direction: column;
            z-index: 1000;
        }

        .settings-panel.open {
            display: flex;
        }

        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .settings-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-high);
            margin: 0;
        }

        .close-btn {
            background: none;
            border: none;
            color: var(--text-mid);
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }

        .close-btn:hover {
            background: var(--input-bg);
            color: var(--text-high);
        }

        .setting-item {
            margin-bottom: 16px;
        }

        .setting-label {
            display: block;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--text-high);
            margin-bottom: 8px;
        }

        .setting-input {
            width: 100%;
            padding: 10px 12px;
            background: var(--input-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            color: var(--text-high);
            font-family: 'Outfit', sans-serif;
            font-size: 0.9rem;
            resize: vertical;
            outline: none;
            transition: border-color 0.2s;
        }

        .setting-input:focus {
            border-color: var(--accent-main);
        }

        .train-btn {
            background: var(--accent-gradient);
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s;
            margin-top: 10px;
        }

        .train-btn:hover {
            transform: translateY(-1px);
        }

        /* --- Main Content --- */
        .main-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            background: radial-gradient(circle at 50% -20%, hsla(260, 80%, 40%, 0.15), transparent);
        }

        header {
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            z-index: 10;
        }

        .engine-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 100px;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            font-size: 0.85rem;
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 10px #10b981;
        }

        /* --- Chat Area --- */
        #chat-wrapper {
            flex: 1;
            overflow-y: auto;
            padding: 20px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .chat-container {
            width: 100%;
            max-width: 850px;
            padding: 0 40px;
        }

        .message {
            margin-bottom: 40px;
            animation: fadeIn 0.4s ease-out;
            width: 100%;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .msg-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--text-high);
        }

        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }

        .user-avatar { background: var(--input-bg); }
        .agent-avatar { background: var(--accent-gradient); box-shadow: 0 0 15px var(--accent-glow); }

        .msg-body {
            padding-left: 44px;
            font-size: 1rem;
            line-height: 1.7;
            color: var(--text-mid);
        }

        .msg-body p { margin-bottom: 16px; }
        .msg-body code {
            font-family: 'JetBrains Mono', monospace;
            background: hsla(0, 0%, 100%, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .msg-body pre {
            background: #0d1117;
            padding: 16px;
            border-radius: 12px;
            margin: 16px 0;
            border: 1px solid var(--glass-border);
            overflow-x: auto;
        }

        /* --- Input Area --- */
        .input-wrapper {
            padding: 24px 40px 40px;
            display: flex;
            justify-content: center;
            background: linear-gradient(to top, var(--bg-dark) 50%, transparent);
        }

        .input-container {
            width: 100%;
            max-width: 850px;
            background: var(--input-bg);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            display: flex;
            align-items: flex-end;
            padding: 12px 16px;
            transition: all 0.3s;
            box-shadow: 0 10px 30px hsla(0, 0%, 0%, 0.3);
        }

        .input-container:focus-within {
            border-color: var(--accent-main);
            box-shadow: 0 0 0 4px var(--accent-glow);
        }

        #query {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-high);
            font-family: 'Outfit', sans-serif;
            font-size: 1.05rem;
            padding: 8px;
            resize: none;
            max-height: 200px;
            outline: none;
        }

        .send-btn {
            background: var(--accent-gradient);
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s;
            margin-left: 10px;
        }

        .send-btn:hover { transform: scale(1.05); }
        .send-btn svg { fill: white; width: 20px; }

        .mic-btn {
            background: transparent;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            margin-right: 5px;
        }

        .mic-btn:hover { background: var(--glass-bg); }
        .mic-btn svg { fill: var(--text-low); width: 22px; transition: fill 0.2s; }
        .mic-btn.recording { background: hsla(0, 80%, 50%, 0.2); }
        .mic-btn.recording svg { fill: #ef4444; animation: mic-pulse 1.5s infinite; }

        .upload-btn {
            background: transparent;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            margin-right: 5px;
        }
        .upload-btn:hover { background: var(--glass-bg); }
        .upload-btn svg { fill: var(--text-low); width: 22px; }

        .file-preview {
            display: none;
            align-items: center;
            gap: 10px;
            padding: 8px 12px;
            background: var(--sidebar-bg);
            border: 1px solid var(--glass-border);
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 0.85rem;
            color: var(--text-mid);
        }
        .file-preview.active { display: flex; }
        .remove-file { cursor: pointer; color: #ef4444; font-size: 1.1rem; }

        @keyframes mic-pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* --- Welcome Screen --- */
        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 0 20px;
        }

        .welcome-title {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(to right, #fff, var(--accent-main));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 16px;
        }

        .welcome-subtitle {
            font-size: 1.1rem;
            color: var(--text-low);
            max-width: 500px;
            line-height: 1.6;
        }

        /* --- Typing Indicator --- */
        .typing {
            display: flex;
            gap: 5px;
            padding: 10px 44px;
        }

        .dot {
            width: 6px;
            height: 6px;
            background: var(--accent-main);
            border-radius: 50%;
            animation: bounce 1.4s infinite;
            opacity: 0.6;
        }

        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-8px); }
        }

        ::-webkit-scrollbar-thumb:hover { background: hsla(230, 20%, 40%, 0.8); }

        @media (max-width: 768px) {
            .sidebar { transform: translateX(-100%); position: absolute; height: 100%; z-index: 100; }
            .chat-container { padding: 0 20px; }
            .welcome-title { font-size: 2.2rem; }
        }
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="logo-area">
            <div class="logo-icon">✨</div>
            <div class="logo-text">AETHER AI</div>
        </div>
        
        <div class="nav-section">
            <span class="section-label">Synchronized Memory</span>
            <div id="memory-list">
                <!-- Memories will appear here -->
                <div class="recent-item"><i>Initializing...</i></div>
            </div>
        </div>

        <div class="sidebar-footer">
            <div class="recent-item" onclick="openSettings()">
                <span>⚙️ Settings</span>
            </div>
        </div>

        <div class="settings-panel" id="settings-panel">
            <div class="settings-header">
                <h3 class="settings-title">Training Settings</h3>
                <button class="close-btn" onclick="closeSettings()">×</button>
            </div>
            <div class="setting-item">
                <label class="setting-label">Topic to Train:</label>
                <input type="text" class="setting-input" id="train-topic" placeholder="e.g., machine learning basics">
            </div>
            <div class="setting-item">
                <label class="setting-label">Knowledge Content:</label>
                <textarea class="setting-input" id="train-content" rows="4" placeholder="Enter the knowledge or information..."></textarea>
            </div>
            <button class="train-btn" onclick="trainKnowledge()">Train Agent</button>
            <div class="setting-item" style="margin-top: 20px; border-top: 1px solid var(--glass-border); padding-top: 20px;">
                <label class="setting-label" style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                    <input type="checkbox" id="tts-toggle" onchange="toggleTTS()"> Auto-Speak Responses (TTS)
                </label>
            </div>
        </div>
    </aside>

    <main class="main-container">
        <header>
            <div style="flex: 1"></div>
            <div class="engine-status" id="model-badge">
                <span class="status-dot"></span>
                Searching for Brain...
            </div>
        </header>

        <section id="chat-wrapper">
            <div class="chat-container">
                <div id="welcome" class="welcome-screen">
                    <h1 class="welcome-title">How can I help you today?</h1>
                    <p class="welcome-subtitle">I'm your autonomous learning assistant. I can browse the live web, research Wikipedia, and evolve with every conversation.</p>
                </div>
                <div id="messages"></div>
                <div id="typing-container" style="display: none;">
                    <div class="typing">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                </div>
            </div>
        </section>

        <div class="input-wrapper" style="flex-direction: column; align-items: center;">
            <div id="file-preview" class="file-preview">
                <span id="file-name">filename.txt</span>
                <span class="remove-file" onclick="clearFile()">×</span>
            </div>
            <div class="input-container">
                <input type="file" id="file-input" style="display: none;" onchange="handleFileSelect()">
                <button class="upload-btn" onclick="document.getElementById('file-input').click()" title="Upload File">
                    <svg viewBox="0 0 24 24"><path d="M16.5,6V17.5A4,4 0 0,1 12.5,21.5A4,4 0 0,1 8.5,17.5V5A2.5,2.5 0 0,1 11,2.5A2.5,2.5 0 0,1 13.5,5V15.5A1,1 0 0,1 12.5,16.5A1,1 0 0,1 11.5,15.5V6H10V15.5A2.5,2.5 0 0,0 12.5,18A2.5,2.5 0 0,0 15,15.5V5A4,4 0 0,0 11,1A4,4 0 0,0 7,5V17.5A5.5,5.5 0 0,0 12.5,23A5.5,5.5 0 0,0 18,17.5V6H16.5Z"></path></svg>
                </button>
                <button class="mic-btn" id="mic-btn" onclick="toggleMic()" title="Voice Input">
                    <svg viewBox="0 0 24 24"><path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"></path></svg>
                </button>
                <textarea id="query" rows="1" placeholder="Deep Research Newton's Law..."></textarea>
                <button class="send-btn" onclick="handleSubmit()">
                    <svg viewBox="0 0 24 24"><path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"></path></svg>
                </button>
            </div>
        </div>
    </main>

    <script>
        const queryInput = document.getElementById('query');
        const messagesContainer = document.getElementById('messages');
        const welcomeScreen = document.getElementById('welcome');
        const typingIndicator = document.getElementById('typing-container');
        const memoryList = document.getElementById('memory-list');
        const modelBadge = document.getElementById('model-badge');
        let isTTSEnabled = false;
        let currentFile = null;

        function handleFileSelect() {
            const input = document.getElementById('file-input');
            if (input.files && input.files[0]) {
                currentFile = input.files[0];
                document.getElementById('file-name').innerText = currentFile.name;
                document.getElementById('file-preview').classList.add('active');
            }
        }

        function clearFile() {
            currentFile = null;
            document.getElementById('file-input').value = '';
            document.getElementById('file-preview').classList.remove('active');
        }

        // Configure Marked
        marked.setOptions({
            highlight: function(code, lang) {
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });

        // Load memory on page load
        window.addEventListener('load', refreshMemory);

        // Auto-resize textarea
        queryInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Enter to send
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
            }
        });

        async function handleSubmit() {
            const query = queryInput.value.trim();
            if (!query) return;

            // Clear input
            queryInput.value = '';
            queryInput.style.height = 'auto';
            welcomeScreen.style.display = 'none';

            addMessage(query, 'user');
            showTyping();

            try {
                let fileContent = null;
                let isImage = false;
                if (currentFile) {
                    const formData = new FormData();
                    formData.append('file', currentFile);
                    const uploadRes = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const uploadData = await uploadRes.json();
                    if (uploadData.success) {
                        fileContent = uploadData.content;
                        isImage = uploadData.is_image;
                    }
                }

                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, file_content: fileContent, is_image: isImage })
                });
                const data = await response.json();
                
                hideTyping();
                clearFile();
                if (data.model) {
                    updateModelBadge(data.model);
                }

                addMessage(data.response, 'agent');
                if (isTTSEnabled) {
                    speakText(data.response);
                }
                refreshMemory();
            } catch (error) {
                hideTyping();
                addMessage("I encountered a connection error. Please ensure the server is running.", 'agent');
            }
        }

        function addMessage(text, role) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${role}`;
            
            const html = `
                <div class="msg-header">
                    <div class="avatar ${role}-avatar">${role === 'user' ? 'U' : '✨'}</div>
                    <span>${role === 'user' ? 'You' : 'Aether AI'}</span>
                    ${role === 'agent' ? `<button class="remove-btn" onclick="speakText(this.parentElement.nextElementSibling.innerText)" style="opacity:1; margin-left:auto; font-size:1.2rem;" title="Speak">🔊</button>` : ''}
                </div>
                <div class="msg-body">
                    ${role === 'agent' ? marked.parse(text) : text.replace(/\\n/g, '<br>')}
                </div>
            `;
            
            msgDiv.innerHTML = html;
            messagesContainer.appendChild(msgDiv);
            
            // Re-highlight if code exists
            msgDiv.querySelectorAll('pre code').forEach((el) => {
                hljs.highlightElement(el);
            });

            const wrapper = document.getElementById('chat-wrapper');
            wrapper.scrollTo({ top: wrapper.scrollHeight, behavior: 'smooth' });
        }

        function showTyping() {
            typingIndicator.style.display = 'block';
            const wrapper = document.getElementById('chat-wrapper');
            wrapper.scrollTo({ top: wrapper.scrollHeight, behavior: 'smooth' });
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        function updateModelBadge(model) {
            const dot = modelBadge.querySelector('.status-dot');
            if (model.includes('Research')) {
                modelBadge.innerHTML = `<span class="status-dot" style="background:#38bdf8; box-shadow:0 0 10px #38bdf8"></span> Mode: Deep Research`;
            } else if (model.includes('Local')) {
                modelBadge.innerHTML = `<span class="status-dot" style="background:#fbbf24; box-shadow:0 0 10px #fbbf24"></span> Mode: Local Engine`;
            } else {
                modelBadge.innerHTML = `<span class="status-dot"></span> Engine: ${model}`;
            }
        }

        async function refreshMemory() {
            console.log('Refreshing memory...');
            try {
                const response = await fetch('/knowledge');
                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Received data:', data);
                const memoryList = document.getElementById('memory-list');
                memoryList.innerHTML = '';
                if (data.topics && data.topics.length > 0) {
                    console.log('Loading', data.topics.length, 'topics');
                    data.topics.forEach(topic => {
                        const item = document.createElement('div');
                        item.className = 'recent-item';
                        item.innerHTML = `
                            <span class="topic-text">🧠 ${topic}</span>
                            <button class="remove-btn" onclick="event.stopPropagation(); removeTopic('${topic.replace(/'/g, "\\'")}')">×</button>
                        `;
                        item.onclick = () => {
                            document.getElementById('query').value = topic;
                            handleSubmit();
                        };
                        memoryList.appendChild(item);
                    });
                } else {
                    console.log('No topics found');
                    const item = document.createElement('div');
                    item.className = 'recent-item';
                    item.innerHTML = `<span>No memories yet</span>`;
                    memoryList.appendChild(item);
                }
            } catch (e) {
                console.error('Failed to refresh memory:', e);
                const memoryList = document.getElementById('memory-list');
                memoryList.innerHTML = '<div class="recent-item"><span>Failed to load memory</span></div>';
            }
        }

        function openSettings() {
            document.getElementById('settings-panel').classList.add('open');
        }

        function closeSettings() {
            document.getElementById('settings-panel').classList.remove('open');
        }

        async function trainKnowledge() {
            const topic = document.getElementById('train-topic').value.trim();
            const content = document.getElementById('train-content').value.trim();

            if (!topic || !content) {
                alert('Please fill in both topic and content fields.');
                return;
            }

            try {
                const response = await fetch('/train', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, content })
                });
                const data = await response.json();

                if (data.success) {
                    alert('✅ Agent trained successfully!');
                    document.getElementById('train-topic').value = '';
                    document.getElementById('train-content').value = '';
                    closeSettings();
                    refreshMemory();
                } else {
                    alert('❌ Training failed: ' + data.error);
                }
            } catch (error) {
                alert('❌ Training failed: ' + error.message);
            }
        }

        async function removeTopic(topic) {
            if (!confirm(`Are you sure you want to remove "${topic}" from memory?`)) {
                return;
            }

            try {
                const response = await fetch('/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic })
                });
                const data = await response.json();

                if (data.success) {
                    alert('✅ Topic removed successfully!');
                    refreshMemory();
                } else {
                    alert('❌ Failed to remove topic: ' + data.error);
                }
            } catch (error) {
                alert('❌ Failed to remove topic: ' + error.message);
            }
        }

        function toggleTTS() {
            isTTSEnabled = document.getElementById('tts-toggle').checked;
        }

        function speakText(text) {
            if (!text) return;
            window.speechSynthesis.cancel();
            const tempDiv = document.createElement('div');
            // Parse markdown to strip formatting for speech
            tempDiv.innerHTML = marked.parse(text);
            const utterance = new SpeechSynthesisUtterance(tempDiv.innerText);
            
            // Optional: Find a nice voice
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) {
                // Prefer a natural sounding English voice if available
                utterance.voice = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en')) || voices[0];
            }
            
            window.speechSynthesis.speak(utterance);
        }

        // --- Voice Recognition (STT) ---
        let recognition;
        let isRecording = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                isRecording = true;
                document.getElementById('mic-btn').classList.add('recording');
                queryInput.placeholder = "Listening...";
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                queryInput.value = transcript;
                handleSubmit(); // Auto-submit the voice query
            };

            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                stopRecording();
            };

            recognition.onend = () => {
                stopRecording();
            };
        }

        function toggleMic() {
            if (!recognition) {
                alert("Speech recognition is not supported in this browser. Try Chrome or Edge.");
                return;
            }
            if (isRecording) {
                recognition.stop();
            } else {
                try {
                    window.speechSynthesis.cancel(); // Stop talking if we start listening
                    recognition.start();
                } catch (e) {
                    console.error("Failed to start recognition:", e);
                }
            }
        }

        function stopRecording() {
            isRecording = false;
            document.getElementById('mic-btn').classList.remove('recording');
            queryInput.placeholder = "Deep Research Newton's Law...";
        }

        // Pre-load voices for TTS
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    user_query = data['query']
    file_content = data.get('file_content')
    if user_query.lower() == 'exit':
        return jsonify({'response': 'Goodbye!', 'learned': None})

    try:
        is_image = data.get('is_image', False)
        response, _, model_name = run_agent(user_query, chat_history, file_content=file_content, is_image=is_image)

        # Update chat history
        chat_history.append(("human", user_query))
        chat_history.append(("assistant", response))

        return jsonify({'response': response, 'learned': None, 'model': model_name})
    except Exception as e:
        logging.error(f"Error for query '{user_query}': {e}")
        return jsonify({'response': f"Error: {str(e)}", 'learned': None})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        content = ""
        is_image = False
        try:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                import base64
                with open(filepath, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                is_image = True
            elif filename.endswith('.pdf'):
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text()
            elif filename.endswith('.docx'):
                doc = Document(filepath)
                content = "\n".join([para.text for para in doc.paragraphs])
            else:
                # Assume text/plain
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            return jsonify({'success': True, 'content': content, 'is_image': is_image})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/knowledge', methods=['GET'])
def get_knowledge():
    try:
        knowledge = load_knowledge()
        # Return top 10 recent topics for UI
        recent_topics = list(knowledge.keys())[-10:]
        return jsonify({'topics': recent_topics})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/train', methods=['POST'])
def train():
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        content = data.get('content', '').strip()

        if not topic or not content:
            return jsonify({'success': False, 'error': 'Topic and content are required'})

        store_knowledge(topic, content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove', methods=['POST'])
def remove():
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()

        if not topic:
            return jsonify({'success': False, 'error': 'Topic is required'})

        if delete_knowledge(topic):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Topic not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n🚀 Starting AI Learning Agent Server...")
    print("📍 Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, host='127.0.0.1', port=5000)

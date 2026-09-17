import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_FILE = "files.json"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

def load_files():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_files(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OX Store | VIP Gaming & Cloud Hub</title>
    
    <link rel="icon" type="image/png" href="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png">
    <link rel="shortcut icon" href="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png">
    <link rel="apple-touch-icon" href="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png">

    <meta name="google-site-verification" content="cstGm0uSsndpI03Pr7_Z3ZJ9VnneQ7PwdK80L1yYfYw" />
    <meta name="description" content="Official OX Store. Fast & verified VIP downloads, configs, and gaming tools.">
    <meta name="keywords" content="ox store, ox cloud, ox cloud hub, oxstore, vip download, ox mods">
    <meta name="robots" content="index, follow">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background-color: #0b0f19;
            color: #f3f4f6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }
        header {
            background: linear-gradient(180deg, rgba(31, 41, 55, 0.7) 0%, rgba(17, 24, 39, 0) 100%);
            padding: 20px 16px;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .header-logo {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #38bdf8;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
        }
        .logo-title {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: 1px;
            background: linear-gradient(90deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .subtitle {
            font-size: 0.82rem;
            color: #9ca3af;
            margin-top: 5px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px 14px;
            width: 100%;
            flex: 1;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        @media (min-width: 768px) {
            .grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
            }
        }
        @media (min-width: 1024px) {
            .grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }
        .card {
            background: #131b2e;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 6px 14px rgba(0,0,0,0.35);
        }
        .card-icon {
            font-size: 1.8rem;
            color: #38bdf8;
            margin-bottom: 8px;
        }
        .card-name {
            font-size: 0.95rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 6px;
            word-break: break-word;
            line-height: 1.3;
        }
        .card-meta {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .btn-download {
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: #ffffff;
            text-align: center;
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.82rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            border: none;
            width: 100%;
            cursor: pointer;
        }
        .empty-box {
            text-align: center;
            color: #6b7280;
            padding: 50px 20px;
            grid-column: span 2;
            font-size: 0.9rem;
        }
        footer {
            text-align: center;
            padding: 18px;
            font-size: 0.8rem;
            color: #9ca3af;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            font-weight: 500;
        }

        /* Modal Backdrop */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(4, 7, 13, 0.85);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 16px;
        }
        .modal-box {
            background: #111827;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 18px;
            width: 100%;
            max-width: 360px;
            padding: 22px 18px;
            text-align: center;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
            animation: modalFadeIn 0.25s ease-out;
        }
        @keyframes modalFadeIn {
            from { transform: scale(0.92); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
        .modal-icon {
            font-size: 2.2rem;
            color: #38bdf8;
            margin-bottom: 8px;
        }
        .modal-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }
        .modal-desc {
            font-size: 0.78rem;
            color: #9ca3af;
            margin-bottom: 18px;
        }
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 18px;
        }
        .task-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 0.82rem;
            font-weight: 600;
            border: 1px solid transparent;
            transition: all 0.25s ease;
            cursor: pointer;
        }
        /* Faded State (Before Click) */
        .task-btn.faded {
            opacity: 0.45;
            filter: grayscale(0.5);
            background: #1f2937;
            color: #d1d5db;
        }
        /* Active / Gadha State (After Click) */
        .task-btn.done {
            opacity: 1;
            filter: grayscale(0);
            box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        }
        .task-yt.done {
            background: linear-gradient(135deg, #b91c1c, #dc2626);
            color: #fff;
        }
        .task-tg.done {
            background: linear-gradient(135deg, #0284c7, #0ea5e9);
            color: #fff;
        }
        .task-ig.done {
            background: linear-gradient(135deg, #c026d3, #db2777);
            color: #fff;
        }

        /* Continue Button */
        .btn-continue {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            font-size: 0.88rem;
            font-weight: 700;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        .btn-continue.locked {
            background: #374151;
            color: #9ca3af;
            cursor: not-allowed;
            opacity: 0.6;
        }
        .btn-continue.unlocked {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ffffff;
            cursor: pointer;
            opacity: 1;
            box-shadow: 0 0 16px rgba(16, 185, 129, 0.4);
        }
        .btn-close {
            margin-top: 10px;
            background: none;
            border: none;
            color: #6b7280;
            font-size: 0.78rem;
            cursor: pointer;
        }

        /* Draggable Support Circle */
        #draggableSupport {
            position: fixed;
            bottom: 30px;
            right: 20px;
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0088cc, #0ea5e9);
            box-shadow: 0 6px 18px rgba(0, 136, 204, 0.5);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #fff;
            text-decoration: none;
            z-index: 99999;
            touch-action: none;
            user-select: none;
            cursor: grab;
            border: 2px solid rgba(255, 255, 255, 0.2);
        }
        #draggableSupport i {
            font-size: 1.25rem;
        }
        #draggableSupport span {
            font-size: 0.58rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 1px;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-title">
            <img src="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png" alt="OX Logo" class="header-logo">
            OX STORE
        </div>
        <div class="subtitle">OX Cloud Hub • VIP Gaming Resources & Direct Access</div>
    </header>

    <div class="container">
        <div class="grid">
            {% if files %}
                {% for f in files %}
                <div class="card">
                    <div>
                        <div class="card-icon"><i class="fa-solid fa-file-shield"></i></div>
                        <div class="card-name">{{ f.name }}</div>
                        <div class="card-meta">
                            <i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Verified Resource
                        </div>
                    </div>
                    <button class="btn-download" onclick="triggerUnlock('{{ f.url }}')">
                        <i class="fa-solid fa-lock"></i> Unlock File
                    </button>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-box">
                    <i class="fa-solid fa-cloud" style="font-size: 2rem; margin-bottom: 8px;"></i><br>
                    No downloads uploaded yet. Use Telegram Bot to upload files.
                </div>
            {% endif %}
        </div>
    </div>

    <!-- Social Lock Modal -->
    <div class="modal-overlay" id="lockModal">
        <div class="modal-box">
            <div class="modal-icon"><i class="fa-solid fa-shield-halved"></i></div>
            <div class="modal-title">Complete 3 Steps</div>
            <div class="modal-desc">Join all channels below to unlock your download link</div>

            <div class="task-list">
                <!-- Task 1: YouTube -->
                <a href="https://youtube.com" target="_blank" class="task-btn faded task-yt" id="taskYt" onclick="completeTask('yt')">
                    <span><i class="fa-brands fa-youtube"></i> Subscribe Channel</span>
                    <i class="fa-regular fa-circle" id="iconYt"></i>
                </a>

                <!-- Task 2: Telegram -->
                <a href="https://t.me" target="_blank" class="task-btn faded task-tg" id="taskTg" onclick="completeTask('tg')">
                    <span><i class="fa-brands fa-telegram"></i> Join Telegram</span>
                    <i class="fa-regular fa-circle" id="iconTg"></i>
                </a>

                <!-- Task 3: Instagram -->
                <a href="https://instagram.com" target="_blank" class="task-btn faded task-ig" id="taskIg" onclick="completeTask('ig')">
                    <span><i class="fa-brands fa-instagram"></i> Follow Instagram</span>
                    <i class="fa-regular fa-circle" id="iconIg"></i>
                </a>
            </div>

            <button class="btn-continue locked" id="btnContinue" onclick="proceedDownload()">
                <i class="fa-solid fa-lock"></i> Locked (0/3)
            </button>
            <br>
            <button class="btn-close" onclick="closeModal()">Cancel</button>
        </div>
    </div>

    <!-- Draggable Support Floating Button -->
    <a href="https://t.me" target="_blank" id="draggableSupport">
        <i class="fa-brands fa-telegram"></i>
        <span>SUPPORT</span>
    </a>

    <footer>
        © 2026 @OxRehann
    </footer>

    <script>
        let targetDownloadUrl = "";
        let tasks = { yt: false, tg: false, ig: false };

        function triggerUnlock(url) {
            targetDownloadUrl = url;
            document.getElementById('lockModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('lockModal').style.display = 'none';
        }

        function completeTask(type) {
            if (type === 'yt') {
                tasks.yt = true;
                const el = document.getElementById('taskYt');
                el.classList.remove('faded');
                el.classList.add('done');
                document.getElementById('iconYt').className = 'fa-solid fa-circle-check';
            } else if (type === 'tg') {
                tasks.tg = true;
                const el = document.getElementById('taskTg');
                el.classList.remove('faded');
                el.classList.add('done');
                document.getElementById('iconTg').className = 'fa-solid fa-circle-check';
            } else if (type === 'ig') {
                tasks.ig = true;
                const el = document.getElementById('taskIg');
                el.classList.remove('faded');
                el.classList.add('done');
                document.getElementById('iconIg').className = 'fa-solid fa-circle-check';
            }

            checkStatus();
        }

        function checkStatus() {
            const count = (tasks.yt ? 1 : 0) + (tasks.tg ? 1 : 0) + (tasks.ig ? 1 : 0);
            const btn = document.getElementById('btnContinue');

            if (count === 3) {
                btn.className = 'btn-continue unlocked';
                btn.innerHTML = '<i class="fa-solid fa-unlock"></i> Continue to Download';
            } else {
                btn.className = 'btn-continue locked';
                btn.innerHTML = `<i class="fa-solid fa-lock"></i> Locked (${count}/3)`;
            }
        }

        function proceedDownload() {
            const count = (tasks.yt ? 1 : 0) + (tasks.tg ? 1 : 0) + (tasks.ig ? 1 : 0);
            if (count === 3 && targetDownloadUrl) {
                window.open(targetDownloadUrl, '_blank');
                closeModal();
            }
        }

        // Draggable Floating Logic
        const dragItem = document.getElementById("draggableSupport");
        let active = false;
        let currentX, currentY, initialX, initialY;
        let xOffset = 0, yOffset = 0;

        dragItem.addEventListener("touchstart", dragStart, {passive: false});
        document.addEventListener("touchend", dragEnd, {passive: false});
        document.addEventListener("touchmove", drag, {passive: false});

        dragItem.addEventListener("mousedown", dragStart);
        document.addEventListener("mouseup", dragEnd);
        document.addEventListener("mousemove", drag);

        function dragStart(e) {
            if (e.type === "touchstart") {
                initialX = e.touches[0].clientX - xOffset;
                initialY = e.touches[0].clientY - yOffset;
            } else {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
            }
            if (e.target === dragItem || dragItem.contains(e.target)) {
                active = true;
            }
        }

        function dragEnd() {
            initialX = currentX;
            initialY = currentY;
            active = false;
        }

        function drag(e) {
            if (active) {
                e.preventDefault();
                if (e.type === "touchmove") {
                    currentX = e.touches[0].clientX - initialX;
                    currentY = e.touches[0].clientY - initialY;
                } else {
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                }
                xOffset = currentX;
                yOffset = currentY;
                setTranslate(currentX, currentY, dragItem);
            }
        }

        function setTranslate(xPos, yPos, el) {
            el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    files = load_files()
    return render_template_string(HTML_TEMPLATE, files=files)

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True)
    if not update or "message" not in update:
        return jsonify({"status": "ignored"}), 200

    msg = update["message"]
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "")

    if text.startswith("/upload"):
        content = text.replace("/upload", "").strip()
        if "|" in content:
            name, url = content.split("|", 1)
            name = name.strip()
            url = url.strip()

            files = load_files()
            files.insert(0, {"name": name, "url": url})
            save_files(files)

            reply = f"✅ Added: {name}"
        else:
            reply = "⚠️ Use format: `/upload File Name | https://download-link.com`"

        if BOT_TOKEN:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": reply, "parse_mode": "Markdown"}
            )

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

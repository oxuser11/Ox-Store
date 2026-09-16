import os
import json
import time
import threading
import telebot
from telebot import types
from flask import Flask, render_template_string, jsonify, request

# ================= CONFIGURATION =================
BOT_TOKEN = "8893917548:AAGdRCp-BrLj1sb74PDKNEtR6N5Lei-tH6E"
ADMIN_ID = 8671410379
ADMIN_USER = "OxRehann"

INSTA_LINK = "https://instagram.com"
TG_CH1_LINK = "https://t.me/OxRehanCyber"
TG_CH2_LINK = "https://t.me/+852hkOgj0UNlZGU9"

DATA_FILE = "web_posts.json"

# ================= PERSISTENT STORAGE =================
def load_posts():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_posts(posts):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(posts, f, indent=2)
    except Exception:
        pass

POSTS = load_posts()

# ================= FLASK WEBSITE =================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OX CLOUD HUB | VIP Downloads</title>
    <meta name="google-site-verification" content="cstGm0uSsndpI03Pr7_Z3ZJ9VnneQ7PwdK80L1yYfYw" />
  
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        body {
            background: #0d1117;
            color: #f0f6fc;
            min-height: 100vh;
            padding-bottom: 60px;
        }
        header {
            background: linear-gradient(135deg, #1f1f38, #0d1117);
            padding: 20px 15px;
            text-align: center;
            border-bottom: 2px solid #30363d;
            box-shadow: 0 4px 20px rgba(0, 255, 204, 0.1);
        }
        .logo {
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, #00f2fe, #4facfe, #00c6ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        .subtitle {
            color: #8b949e;
            font-size: 0.8rem;
            margin-top: 4px;
        }
        .search-container {
            max-width: 500px;
            margin: 15px auto 5px;
            position: relative;
            padding: 0 10px;
        }
        .search-box {
            width: 100%;
            padding: 10px 15px 10px 40px;
            background: #161b22;
            border: 1.5px solid #30363d;
            border-radius: 50px;
            color: #fff;
            font-size: 0.9rem;
            outline: none;
            transition: 0.3s;
        }
        .search-box:focus {
            border-color: #00f2fe;
            box-shadow: 0 0 12px rgba(0, 242, 254, 0.3);
        }
        .search-icon {
            position: absolute;
            left: 24px;
            top: 50%;
            transform: translateY(-50%);
            color: #8b949e;
            font-size: 0.9rem;
        }

        /* COMPACT GRID FOR MOBILE (2 CARDS PER ROW) */
        .container {
            max-width: 1100px;
            margin: 15px auto;
            padding: 0 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        @media (min-width: 768px) {
            .grid {
                grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
                gap: 20px;
            }
        }
        .card {
            background: #161b22;
            border-radius: 14px;
            border: 1px solid #30363d;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            transition: 0.3s;
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, #ff0844, #ffb199, #00f2fe);
        }
        .card img {
            width: 55px;
            height: 55px;
            border-radius: 14px;
            object-fit: cover;
            margin-bottom: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            border: 1.5px solid #30363d;
        }
        .card h3 {
            font-size: 0.92rem;
            color: #f0f6fc;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
        }
        .card p {
            color: #8b949e;
            font-size: 0.72rem;
            line-height: 1.3;
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            flex-grow: 1;
        }
        .btn-download {
            width: 100%;
            padding: 8px 10px;
            background: linear-gradient(135deg, #00f2fe, #4facfe);
            border: none;
            border-radius: 8px;
            color: #0d1117;
            font-weight: 700;
            font-size: 0.8rem;
            cursor: pointer;
            transition: 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .btn-download:hover {
            opacity: 0.9;
        }
        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 50px 20px;
            color: #8b949e;
        }

        /* MODAL POPUP */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 999;
            padding: 15px;
        }
        .modal {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 18px;
            max-width: 380px;
            width: 100%;
            padding: 20px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            position: relative;
        }
        .modal h2 {
            font-size: 1.25rem;
            margin-bottom: 6px;
            color: #fff;
        }
        .modal p {
            font-size: 0.8rem;
            color: #8b949e;
            margin-bottom: 15px;
        }
        .social-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 10px;
            border-radius: 10px;
            text-decoration: none;
            color: #fff;
            font-weight: 600;
            font-size: 0.88rem;
            margin-bottom: 10px;
            transition: 0.3s;
            border: none;
        }
        .btn-insta { background: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888); }
        .btn-tg1 { background: linear-gradient(135deg, #0088cc, #00c6ff); }
        .btn-tg2 { background: linear-gradient(135deg, #8e2de2, #4a00e0); }
        .btn-final {
            background: #238636;
            opacity: 0.4;
            pointer-events: none;
            margin-top: 10px;
        }
        .btn-final.unlocked {
            opacity: 1;
            pointer-events: auto;
            background: linear-gradient(135deg, #2ea043, #238636);
            box-shadow: 0 0 12px rgba(46, 160, 67, 0.4);
        }
        .close-btn {
            position: absolute;
            top: 12px;
            right: 15px;
            background: transparent;
            border: none;
            color: #8b949e;
            font-size: 1.3rem;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">⚡ OX CLOUD STORE ⚡</div>
        <div class="subtitle">Official VIP Access & Verified Fast Downloads</div>
        <div class="search-container">
            <i class="fa fa-search search-icon"></i>
            <input type="text" id="searchBox" class="search-box" placeholder="Search files..." onkeyup="filterApps()">
        </div>
    </header>

    <div class="container">
        <div class="grid" id="appsGrid">
            {% if not posts %}
            <div class="empty-state">
                <i class="fa fa-box-open" style="font-size: 2.5rem; margin-bottom: 10px;"></i>
                <h3>No Files Uploaded!</h3>
                <p>Use Telegram Bot /upload to publish files.</p>
            </div>
            {% endif %}
            {% for item in posts %}
            <div class="card app-card" data-title="{{ item.name.lower() }}" data-desc="{{ item.desc.lower() }}">
                <img src="{{ item.icon }}" alt="Icon" onerror="this.src='https://cdn-icons-png.flaticon.com/512/831/831381.png'">
                <h3>{{ item.name }}</h3>
                <p>{{ item.desc }}</p>
                <button class="btn-download" onclick="openGate('{{ item.file_link }}')">
                    <i class="fa fa-download"></i> Get File
                </button>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="modal-overlay" id="gateModal">
        <div class="modal">
            <button class="close-btn" onclick="closeGate()">&times;</button>
            <h2>🔒 Unlock Download</h2>
            <p>Complete the actions to unlock your file.</p>

            <a href="{{ insta_link }}" target="_blank" class="social-btn btn-insta" onclick="markStep(1)">
                <i class="fab fa-instagram"></i> Follow on Instagram
            </a>
            <a href="{{ tg1_link }}" target="_blank" class="social-btn btn-tg1" onclick="markStep(2)">
                <i class="fab fa-telegram"></i> Join Telegram Channel 1
            </a>
            <a href="{{ tg2_link }}" target="_blank" class="social-btn btn-tg2" onclick="markStep(3)">
                <i class="fab fa-telegram"></i> Join Telegram Channel 2
            </a>

            <a id="continueBtn" href="#" target="_blank" class="social-btn btn-final">
                <i class="fa fa-unlock"></i> Continue to Download
            </a>
        </div>
    </div>

    <script>
        function filterApps() {
            let input = document.getElementById('searchBox').value.toLowerCase();
            let cards = document.getElementsByClassName('app-card');
            for (let i = 0; i < cards.length; i++) {
                let title = cards[i].getAttribute('data-title');
                let desc = cards[i].getAttribute('data-desc');
                if (title.includes(input) || desc.includes(input)) {
                    cards[i].style.display = "flex";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }

        let completed = { 1: false, 2: false, 3: false };
        let activeFile = "";

        function openGate(fileLink) {
            activeFile = fileLink;
            document.getElementById('gateModal').style.display = 'flex';
        }

        function closeGate() {
            document.getElementById('gateModal').style.display = 'none';
        }

        function markStep(step) {
            completed[step] = true;
            if (completed[1] && completed[2] && completed[3]) {
                let btn = document.getElementById('continueBtn');
                btn.classList.add('unlocked');
                btn.href = activeFile;
                btn.innerHTML = '<i class="fa fa-download"></i> Continue to Download';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(
        HTML_TEMPLATE,
        posts=POSTS,
        insta_link=INSTA_LINK,
        tg1_link=TG_CH1_LINK,
        tg2_link=TG_CH2_LINK
    )

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= TELEGRAM ADMIN BOT =================
bot = telebot.TeleBot(BOT_TOKEN, skip_pending=True)
try:
    bot.remove_webhook()
except Exception:
    pass

admin_sessions = {}

@bot.message_handler(commands=['start'])
def start_bot(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "⛔ <b>Access Denied!</b> This is a private web control bot.", parse_mode='HTML')
        return

    msg = (
        f"👑 <b>OX WEBSITE ADMIN PANEL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Aap yahan se directly website par files upload kar sakte hain.\n\n"
        f"Commands:\n"
        f"👉 /upload - Naya app ya file publish karein\n"
        f"👉 /list - Live uploaded items dekhein\n"
        f"👉 /delete &lt;id&gt; - Koi post delete karein\n"
        f"👉 /cancel - Current action cancel karein\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    bot.reply_to(m, msg, parse_mode='HTML')

@bot.message_handler(commands=['cancel'])
def cancel_op(m):
    if m.from_user.id == ADMIN_ID:
        admin_sessions.pop(ADMIN_ID, None)
        bot.reply_to(m, "❌ Action cancelled.")

@bot.message_handler(commands=['upload'])
def init_upload(m):
    if m.from_user.id != ADMIN_ID:
        return
    admin_sessions[ADMIN_ID] = {"step": "WAIT_FILE"}
    bot.send_message(
        m.chat.id,
        "📁 <b>STEP 1: File bhejiye</b>\n\nJo APK, ZIP, ya Document user ko download karwana hai, use yahan send karein.\n<i>(Cancel ke liye /cancel likhein)</i>",
        parse_mode='HTML'
    )

@bot.message_handler(content_types=['document', 'audio', 'video'], func=lambda m: admin_sessions.get(m.from_user.id, {}).get("step") == "WAIT_FILE")
def get_file(m):
    doc = m.document or m.audio or m.video
    file_id = doc.file_id
    f_info = bot.get_file(file_id)
    direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{f_info.file_path}"

    admin_sessions[ADMIN_ID]["file_link"] = direct_link
    admin_sessions[ADMIN_ID]["file_name"] = getattr(doc, 'file_name', 'Download File')
    admin_sessions[ADMIN_ID]["step"] = "WAIT_ICON"

    bot.send_message(
        m.chat.id,
        "🖼️ <b>STEP 2: Icon Image Link bhejiye</b>\n\nWeb card par jo logo/icon dikhana hai uska image link (URL) paste karein:\n<i>(Example: https://i.imgur.com/xyz.png)</i>",
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda m: admin_sessions.get(m.from_user.id, {}).get("step") == "WAIT_ICON")
def get_icon(m):
    url = m.text.strip()
    if not url.startswith("http"):
        bot.reply_to(m, "⚠️ Kripya valid http ya https image URL bhejein!")
        return

    admin_sessions[ADMIN_ID]["icon"] = url
    admin_sessions[ADMIN_ID]["step"] = "WAIT_NAME"
    bot.send_message(m.chat.id, "🏷️ <b>STEP 3: App / File Name bhejiye</b>\n\nJaise: <code>Free Fire Max Sensitivity VIP</code>", parse_mode='HTML')

@bot.message_handler(func=lambda m: admin_sessions.get(m.from_user.id, {}).get("step") == "WAIT_NAME")
def get_name(m):
    admin_sessions[ADMIN_ID]["name"] = m.text.strip()
    admin_sessions[ADMIN_ID]["step"] = "WAIT_DESC"
    bot.send_message(m.chat.id, "📝 <b>STEP 4: Short Description bhejiye</b>\n\nJaise: <code>100% Headshot config with smooth fps support.</code>", parse_mode='HTML')

@bot.message_handler(func=lambda m: admin_sessions.get(m.from_user.id, {}).get("step") == "WAIT_DESC")
def get_desc(m):
    sess = admin_sessions[ADMIN_ID]
    sess["desc"] = m.text.strip()

    preview = (
        f"📋 <b>PREVIEW CARD FOR WEBSITE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Title:</b> {sess['name']}\n"
        f"📝 <b>Desc:</b> {sess['desc']}\n"
        f"🖼️ <b>Icon:</b> {sess['icon']}\n"
        f"📦 <b>File:</b> {sess['file_name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Kya ise website par live publish karna hai?"
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🚀 Publish Now", callback_data="pub_confirm"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="pub_cancel")
    )
    bot.send_message(m.chat.id, preview, parse_mode='HTML', reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data in ["pub_confirm", "pub_cancel"])
def publish_callback(c):
    if c.from_user.id != ADMIN_ID:
        return

    if c.data == "pub_confirm":
        sess = admin_sessions.pop(ADMIN_ID, None)
        if not sess:
            bot.answer_callback_query(c.id, "Session expired!")
            return

        new_item = {
            "id": int(time.time()),
            "name": sess["name"],
            "desc": sess["desc"],
            "icon": sess["icon"],
            "file_link": sess["file_link"]
        }
        POSTS.insert(0, new_item)
        save_posts(POSTS)

        bot.edit_message_text(
            f"🎉 <b>Successfully Published to Website!</b>\n\nNaya card live ho chuka hai.",
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            parse_mode='HTML'
        )
    else:
        admin_sessions.pop(ADMIN_ID, None)
        bot.edit_message_text("❌ Cancel kar diya gaya.", chat_id=c.message.chat.id, message_id=c.message.message_id)

@bot.message_handler(commands=['list'])
def list_items(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not POSTS:
        bot.reply_to(m, "Web page par abhi koi file nahi hai.")
        return

    out = "📂 <b>CURRENT WEBSITE POSTS:</b>\n\n"
    for item in POSTS:
        out += f"• <code>{item['id']}</code> : <b>{item['name']}</b>\n"
    out += "\nDelete karne ke liye: <code>/delete &lt;id&gt;</code>"
    bot.reply_to(m, out, parse_mode='HTML')

@bot.message_handler(commands=['delete'])
def delete_item(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(m, "Format: <code>/delete 1726000000</code>", parse_mode='HTML')
        return

    target_id = int(parts[1])
    global POSTS
    before = len(POSTS)
    POSTS = [p for p in POSTS if p["id"] != target_id]

    if len(POSTS) < before:
        save_posts(POSTS)
        bot.reply_to(m, f"✅ Item <code>{target_id}</code> removed from website!", parse_mode='HTML')
    else:
        bot.reply_to(m, "❌ ID nahi mili.", parse_mode='HTML')

# ================= MAIN RUNNER =================
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    

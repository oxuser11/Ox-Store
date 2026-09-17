import os, json, html, secrets
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, redirect, render_template_string, request, abort

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

FILES_DB = os.path.join(DATA, "files.json")
USERS_DB = os.path.join(DATA, "users.json")
SETTINGS_DB = os.path.join(DATA, "settings.json")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8893917548:AAGdRCp-BrLj1sb74PDKNEtR6N5Lei-tH6E")
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "8671410379"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-this-secret")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ox-store-sdhv.onrender.com/webhook")
CHANNEL_URL = os.getenv("TELEGRAM_CHANNEL_URL", "https://t.me/+852hkOgj0UNlZGU9")
VIP_URL = os.getenv("VIP_GROUP_URL", "https://t.me/OxRehanCyber")
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/OxRehann")
YOUTUBE_URL = os.getenv("YOUTUBE_URL", "https://youtube.com/@UK-EDITSSS")
PORT = int(os.getenv("PORT", "10000"))

USER_STATES = {}

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path, default):
    try:
        if not os.path.exists(path):
            save(path, default)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def reindex_files(items):
    for index, item in enumerate(items, start=1):
        item["id"] = str(index)
    save(FILES_DB, items)
    return items

def get_files():
    data = load(FILES_DB, [])
    # Ensure sequential IDs are preserved
    needs_save = False
    for idx, item in enumerate(data, start=1):
        if str(item.get("id")) != str(idx):
            item["id"] = str(idx)
            needs_save = True
    if needs_save:
        save(FILES_DB, data)
    return data

def get_users(): return load(USERS_DB, {})

def get_settings():
    default = {"tasks":{"1":CHANNEL_URL,"2":YOUTUBE_URL,"3":VIP_URL}}
    x = load(SETTINGS_DB, default)
    x.setdefault("tasks", {})
    for k,v in default["tasks"].items(): x["tasks"].setdefault(k,v)
    save(SETTINGS_DB, x)
    return x

def tg(method, data=None, files=None):
    if not BOT_TOKEN:
        return {"ok":False,"description":"Bot token missing"}
    try:
        r = requests.post("https://api.telegram.org/bot"+BOT_TOKEN+"/"+method,
                          data=data or {}, files=files, timeout=25)
        return r.json()
    except Exception as e:
        return {"ok":False,"description":str(e)}

def send(chat_id, text, markup=None):
    data = {"chat_id":chat_id, "text":text, "parse_mode":"HTML", "disable_web_page_preview":True}
    if markup: data["reply_markup"] = json.dumps(markup)
    return tg("sendMessage", data)

def keyboard():
    return {"keyboard":[
        [{"text":"➕ Upload File"},{"text":"📊 Total Stats"}],
        [{"text":"📋 List All Files"},{"text":"⚡ All Commands"}]
    ],"resize_keyboard":True}

def is_admin(chat_id): 
    return str(chat_id) == ADMIN_ID or not ADMIN_ID

def register(message):
    u = message.get("from", {}); uid = str(u.get("id", ""))
    if not uid: return
    users = get_users()
    users[uid] = {"id":u.get("id"), "username":u.get("username",""),
                  "first_name":u.get("first_name",""), "last_name":u.get("last_name",""),
                  "last_seen":now()}
    save(USERS_DB, users)

def add_file(name, url, icon="", desc=""):
    items = get_files()
    new_id = str(len(items) + 1)
    x = {
        "id": new_id,
        "name": name.strip(),
        "url": url.strip(),
        "icon": icon.strip() or "https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png",
        "desc": desc.strip() or "VIP Resource Direct Access",
        "downloads": 0,
        "created_at": now(),
        "updated_at": now()
    }
    items.append(x)
    save(FILES_DB, items)
    return x

def delete_file_by_id(target_id):
    items = get_files()
    found = False
    new_items = []
    for x in items:
        if str(x.get("id")) == str(target_id):
            found = True
        else:
            new_items.append(x)
    if not found:
        return False, len(items)
    # Auto re-index so next files shift up
    reindex_files(new_items)
    return True, len(new_items)

def help_text():
    return """⚡ <b>OX STORE BOT - ADMIN PANEL</b>

<b>Commands & Usage:</b>
• <b>➕ Upload File</b> - Interactive step-by-step upload
• <code>/list</code> - View all files with sequential numbers (1, 2, 3...)
• <code>/delete &lt;number&gt;</code> - Delete a file (remaining files auto-shift)
• <code>/edit &lt;number&gt;</code> - Modify name/URL of existing item
• <code>/stats</code> - View live views & total downloads
• <code>/clearall</code> - Wipe all resources from store
• <code>/setkey 1 | URL</code> - Change Task 1 (Telegram)
• <code>/setkey 2 | URL</code> - Change Task 2 (YouTube)
• <code>/setkey 3 | URL</code> - Change Task 3 (VIP Group)
• <code>/broadcast Message</code> - Send message to all users
• <code>/cancel</code> - Cancel ongoing upload/edit operation"""

def process(message, text):
    chat_id = message["chat"]["id"]
    uid = str(chat_id)
    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower(); arg = arg.strip()

    if cmd == "/cancel":
        USER_STATES.pop(uid, None)
        send(chat_id, "🚫 <b>Operation cancelled.</b>", keyboard())
        return

    # Handle Interactive Multi-step operations
    if uid in USER_STATES:
        state = USER_STATES[uid]
        step = state.get("step")

        if step == "WAIT_URL":
            state["url"] = text.strip()
            state["step"] = "WAIT_ICON"
            send(chat_id, "🖼️ <b>Step 2/4: Icon URL bhejo</b>\n\nDirect image link paste karein ya default icon ke liye <code>skip</code> type karein:",
                 {"keyboard": [[{"text":"skip"}],[{"text":"/cancel"}]], "resize_keyboard":True})
            return

        if step == "WAIT_ICON":
            state["icon"] = "" if text.lower() == "skip" else text.strip()
            state["step"] = "WAIT_NAME"
            send(chat_id, "🏷️ <b>Step 3/4: File Name bhejo</b>\n\nWebsite par dikhane ke liye title type karein:",
                 {"keyboard": [[{"text":"/cancel"}]], "resize_keyboard":True})
            return

        if step == "WAIT_NAME":
            state["name"] = text.strip()
            state["step"] = "WAIT_DESC"
            send(chat_id, "📝 <b>Step 4/4: Description bhejo</b>\n\nShort note type karein ya default ke liye <code>skip</code> bhejein:",
                 {"keyboard": [[{"text":"skip"}],[{"text":"/cancel"}]], "resize_keyboard":True})
            return

        if step == "WAIT_DESC":
            state["desc"] = "" if text.lower() == "skip" else text.strip()
            state["step"] = "CONFIRM"
            
            preview = f"""📦 <b>Preview New Item:</b>
━━━━━━━━━━━━━━━━━━━━
🏷️ <b>Title:</b> {html.escape(state['name'])}
🔗 <b>Target URL:</b> {html.escape(state['url'])}
🖼️ <b>Icon:</b> {html.escape(state.get('icon') or 'Default')}
📝 <b>Description:</b> {html.escape(state.get('desc') or 'Default')}
━━━━━━━━━━━━━━━━━━━━
Kya is file ko store par live karna hai?"""

            markup = {
                "inline_keyboard": [
                    [{"text": "🌐 Publish Now", "callback_data": "pub_yes"}],
                    [{"text": "❌ Cancel", "callback_data": "pub_no"}]
                ]
            }
            send(chat_id, preview, markup)
            return

        if step == "EDIT_NAME":
            state["name"] = text.strip()
            state["step"] = "EDIT_URL"
            send(chat_id, "🔗 <b>Naya Download URL bhejo</b> (ya purana rakhne ke liye <code>skip</code> likhein):",
                 {"keyboard": [[{"text":"skip"}],[{"text":"/cancel"}]], "resize_keyboard":True})
            return

        if step == "EDIT_URL":
            items = get_files()
            target_id = state.get("target_id")
            for x in items:
                if str(x.get("id")) == str(target_id):
                    x["name"] = state["name"]
                    if text.lower() != "skip":
                        x["url"] = text.strip()
                    x["updated_at"] = now()
                    break
            save(FILES_DB, items)
            USER_STATES.pop(uid, None)
            send(chat_id, f"✅ <b>File #{target_id} updated successfully!</b>", keyboard())
            return

    if cmd in ("/start", "/help"):
        send(chat_id, help_text(), keyboard()); return
    if cmd == "/ping":
        send(chat_id, "🏓 <b>Pong!</b> OX Store core is live.", keyboard()); return

    if not is_admin(chat_id):
        send(chat_id, "⛔ <b>Admin only access.</b>"); return

    if cmd == "/upload" or text == "➕ Upload File":
        USER_STATES[uid] = {"step": "WAIT_URL"}
        send(chat_id, "🚀 <b>Step 1/4: File / Download URL bhejo</b>\n\nJo download link store par attach karni hai wo send karein:",
             {"keyboard": [[{"text":"/cancel"}]], "resize_keyboard":True})
        return

    if cmd in ("/delete", "/delet"):
        if not arg:
            send(chat_id, "❌ File number specify karein.\nExample: <code>/delete 5</code>"); return
        success, count = delete_file_by_id(arg)
        if not success:
            send(chat_id, f"❌ File #{arg} nahi mili. List check karne ke liye <code>/list</code> use karein.")
        else:
            send(chat_id, f"🗑️ <b>File #{arg} delete kar di gayi hai!</b>\nBaaki files automatically count me upar shift ho gayi hain.\nTotal live files: <b>{count}</b>", keyboard())
        return

    if cmd == "/edit":
        if not arg:
            send(chat_id, "❌ File number specify karein.\nExample: <code>/edit 2</code>"); return
        items = get_files()
        target = next((x for x in items if str(x.get("id")) == arg), None)
        if not target:
            send(chat_id, f"❌ File #{arg} nahi mili."); return
        USER_STATES[uid] = {"step": "EDIT_NAME", "target_id": arg}
        send(chat_id, f"✏️ <b>Editing File #{arg}: {html.escape(target['name'])}</b>\n\nNaya <b>File Name</b> type karke bhejein:",
             {"keyboard": [[{"text":"/cancel"}]], "resize_keyboard":True})
        return

    if cmd == "/list" or text == "📋 List All Files":
        items = get_files()
        if not items:
            send(chat_id, "📭 <b>Koi files active nahi hain.</b>", keyboard()); return
        body = []
        for x in items:
            body.append(f"<b>#{x['id']}</b> • <b>{html.escape(str(x['name']))}</b>\n🔗 {html.escape(x['url'])}")
        send(chat_id, "📋 <b>ALL STORE FILES (SEQUENTIAL)</b>\n━━━━━━━━━━━━━━━━━━━━\n" + "\n\n".join(body), keyboard()); return

    if cmd == "/stats" or text == "📊 Total Stats":
        items = get_files(); total = sum(int(x.get("downloads",0)) for x in items)
        send(chat_id, f"📊 <b>OX STORE LIVE METRICS</b>\n\n📦 Active Files: <b>{len(items)}</b>\n⬇️ Total Downloads: <b>{total}</b>\n👥 Total Users: <b>{len(get_users())}</b>", keyboard()); return

    if cmd == "/clearall":
        send(chat_id, "⚠️ <b>Saari files delete karni hain?</b>", {"inline_keyboard":[[
            {"text":"✅ YES, DELETE ALL","callback_data":"clear_yes"},
            {"text":"❌ CANCEL","callback_data":"clear_no"}]]}); return

    if cmd == "/setkey":
        p = [x.strip() for x in arg.split("|", 1)]
        if len(p) != 2 or p[0] not in ("1","2","3") or not p[1]:
            send(chat_id, "❌ Use: <code>/setkey 1 | URL</code>"); return
        s = get_settings(); s["tasks"][p[0]] = p[1]; save(SETTINGS_DB, s)
        send(chat_id, f"✅ <b>Task {p[0]} link update ho gaya.</b>", keyboard()); return

    if cmd == "/broadcast":
        if not arg: send(chat_id, "❌ Use: <code>/broadcast Message</code>"); return
        sent = 0
        for u in get_users():
            if tg("sendMessage", {"chat_id":u, "text":html.escape(arg), "parse_mode":"HTML"}).get("ok"): sent += 1
        send(chat_id, f"📢 Broadcast complete! Delivered to <b>{sent}</b> users.", keyboard()); return

    send(chat_id, "❓ Samajh nahi aaya. Button use karein ya /help bhejein.", keyboard())

@app.post("/webhook")
def webhook():
    supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if WEBHOOK_SECRET and not secrets.compare_digest(supplied, WEBHOOK_SECRET): abort(403)
    update = request.get_json(silent=True) or {}
    try:
        if "callback_query" in update:
            q = update["callback_query"]
            chat_id = q.get("message", {}).get("chat", {}).get("id")
            uid = str(chat_id)
            tg("answerCallbackQuery", {"callback_query_id": q.get("id")})

            if q.get("data") == "pub_yes" and uid in USER_STATES:
                st = USER_STATES.pop(uid)
                x = add_file(st["name"], st["url"], st.get("icon", ""), st.get("desc", ""))
                send(chat_id, f"🎉 <b>File Live Kar Di Gayi Hai!</b>\n\n🔢 <b>Assigned Number:</b> #{x['id']}\n📦 <b>Name:</b> {html.escape(x['name'])}\n🌐 <b>Live on Web:</b> {WEBHOOK_URL.replace('/webhook','')}", keyboard())
                return jsonify(ok=True)
            elif q.get("data") == "pub_no":
                USER_STATES.pop(uid, None)
                send(chat_id, "❌ Upload cancel ho gaya.", keyboard())
                return jsonify(ok=True)

            if q.get("data") == "clear_yes" and is_admin(chat_id):
                save(FILES_DB, []); send(chat_id, "🗑️ Saari files clear kar di gayi hain.", keyboard())
            elif q.get("data") == "clear_no":
                send(chat_id, "❎ Action cancelled.", keyboard())
            return jsonify(ok=True)

        message = update.get("message")
        if not message: return jsonify(ok=True)
        register(message)
        text = message.get("text", "").strip()
        if text == "⚡ All Commands":
            send(message["chat"]["id"], help_text(), keyboard())
        else:
            process(message, text)
    except Exception as e:
        print("Webhook Error:", e)
    return jsonify(ok=True)

@app.get("/set-webhook")
def set_webhook():
    if not WEBHOOK_URL: return jsonify(ok=False, error="WEBHOOK_URL missing"), 400
    return jsonify(tg("setWebhook", {"url":WEBHOOK_URL, "secret_token":WEBHOOK_SECRET, "drop_pending_updates":True}))

@app.get("/telegram-status")
def telegram_status(): return jsonify(tg("getMe"))

@app.get("/api/files")
def api_files():
    # Website receives file details without exposing numeric counts/IDs
    return jsonify([{
        "name": x.get("name"),
        "url": x.get("url"),
        "icon": x.get("icon"),
        "desc": x.get("desc"),
        "downloads": x.get("downloads", 0),
        "id": x.get("id")
    } for x in get_files()])

@app.get("/api/tasks")
def api_tasks(): return jsonify(get_settings()["tasks"])

@app.get("/download/<file_id>")
def download(file_id):
    items = get_files()
    for x in items:
        if str(x.get("id")) == str(file_id):
            x["downloads"] = int(x.get("downloads", 0)) + 1
            x["updated_at"] = now()
            save(FILES_DB, items)
            return redirect(x["url"])
    abort(404)

PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#070a12"><title>OX Store | VIP Gaming & Cloud Hub</title>
<link rel="icon" href="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png">
<style>
*{box-sizing:border-box}body{margin:0;color:#f7f9ff;font-family:Inter,system-ui,Arial;background:radial-gradient(circle at 15% 5%,#7c5cff2d,transparent 30%),radial-gradient(circle at 85% 20%,#00d4ff20,transparent 28%),#070a12}.wrap{width:min(1180px,calc(100% - 24px));margin:auto}header{position:sticky;top:0;z-index:20;background:#070a12d0;backdrop-filter:blur(18px);border-bottom:1px solid #ffffff1b}.nav{min-height:76px;display:flex;align-items:center;gap:13px}.logo{width:48px;height:48px;border-radius:50%;object-fit:cover}.brand h1{margin:0;font-size:22px;background:linear-gradient(90deg,#fff,#8e7bff,#00d4ff);-webkit-background-clip:text;color:transparent}.brand p{margin:4px 0 0;color:#aab3c7;font-size:11px}.hero{text-align:center;padding:44px 0 22px}.hero h2{font-size:clamp(30px,6vw,58px);margin:0 0 10px;letter-spacing:-2px}.hero h2 span{background:linear-gradient(90deg,#fff,#8e7bff,#00d4ff);-webkit-background-clip:text;color:transparent}.hero p{color:#aab3c7}.search{max-width:720px;margin:25px auto}.search input{width:100%;padding:17px 20px;border-radius:18px;border:1px solid #ffffff1c;background:#ffffff0d;color:white;outline:0;font-size:15px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding-bottom:60px}.card{display:flex;flex-direction:column;align-items:flex-start;padding:18px;border:1px solid #ffffff1c;border-radius:21px;background:#ffffff09;backdrop-filter:blur(14px);transition:.2s}.card:hover{transform:translateY(-4px);border-color:#8e7bff88}.card-header{display:flex;align-items:center;gap:12px;margin-bottom:12px;width:100%}.card-icon{width:46px;height:46px;border-radius:14px;object-fit:cover;background:#ffffff15;border:1px solid #ffffff25}.badge{font-size:10px;padding:4px 8px;border-radius:20px;background:#7c5cff25;color:#c7bdff;font-weight:700}.card h3{margin:8px 0 4px;font-size:16px;word-break:break-word}.card p{margin:0 0 16px;font-size:12px;color:#aab3c7;line-height:1.4}.card .meta{font-size:11px;color:#6b7280;margin-top:auto;padding-bottom:12px}.btn{width:100%;border:0;border-radius:13px;padding:12px;color:white;font-weight:800;background:linear-gradient(100deg,#7657ff,#00aeea);cursor:pointer}.empty{grid-column:1/-1;text-align:center;padding:45px;border:1px dashed #ffffff25;border-radius:18px;color:#aab3c7}footer{text-align:center;border-top:1px solid #ffffff1c;padding:27px;color:#8d96a9;font-size:12px}.support{position:fixed;right:16px;bottom:16px;z-index:30;width:62px;height:62px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:linear-gradient(145deg,#20a7ff,#6956ff);box-shadow:0 15px 40px #0008;cursor:grab;touch-action:none;user-select:none}.support span{font-size:8px;font-weight:800}.overlay{position:fixed;inset:0;z-index:50;background:#000b;backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;padding:18px}.overlay.show{display:flex}.modal{width:min(460px,100%);padding:22px;border:1px solid #ffffff1c;border-radius:25px;background:#101725}.modal h3{margin:0 0 7px}.sub{font-size:12px;color:#aab3c7}.task{display:flex;align-items:center;gap:12px;padding:13px;margin:10px 0;border:1px solid #ffffff1c;border-radius:16px;background:#ffffff08;cursor:pointer}.task.done{border-color:#20e58a88;background:#20e58a12}.icon{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:#7c5cff1d}.task small{display:block;color:#aab3c7;font-size:10px}.check{margin-left:auto;font-size:20px}.done .check{color:#20e58a}.actions{display:flex;gap:10px;margin-top:18px}.close{padding:12px 16px;border-radius:13px;background:#ffffff0d;color:white;border:1px solid #ffffff1c}.unlock{flex:1;opacity:.45}.unlock.ready{opacity:1}.toast{position:fixed;left:50%;bottom:25px;transform:translateX(-50%) translateY(20px);opacity:0;z-index:80;padding:12px 16px;border-radius:13px;background:#111827;border:1px solid #ffffff1c;font-size:12px;transition:.2s}.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}@media(max-width:950px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:680px){.grid{grid-template-columns:repeat(2,1fr);gap:10px}.wrap{width:calc(100% - 16px)}.logo{width:42px;height:42px}.brand h1{font-size:18px}.brand p{font-size:9px}.hero{padding:34px 0 12px}.card{padding:13px}.card h3{font-size:1

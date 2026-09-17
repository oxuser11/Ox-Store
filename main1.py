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
YOUTUBE_URL = os.getenv("YOUTUBE_URL", "https://youtube.com/")
PORT = int(os.getenv("PORT", "10000"))

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

def get_files(): return load(FILES_DB, [])
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
        r=requests.post("https://api.telegram.org/bot"+BOT_TOKEN+"/"+method,
                        data=data or {},files=files,timeout=25)
        return r.json()
    except Exception as e:
        return {"ok":False,"description":str(e)}

def send(chat_id,text,markup=None):
    data={"chat_id":chat_id,"text":text,"parse_mode":"HTML","disable_web_page_preview":True}
    if markup: data["reply_markup"]=json.dumps(markup)
    return tg("sendMessage",data)

def keyboard():
    return {"keyboard":[
        [{"text":"➕ Upload File"},{"text":"📊 Total Stats"}],
        [{"text":"📋 List All Files"},{"text":"⚡ All Commands"}]
    ],"resize_keyboard":True}

def is_admin(chat_id): return str(chat_id)==ADMIN_ID

def register(message):
    u=message.get("from",{});uid=str(u.get("id",""))
    if not uid:return
    users=get_users()
    users[uid]={"id":u.get("id"),"username":u.get("username",""),
                "first_name":u.get("first_name",""),"last_name":u.get("last_name",""),
                "last_seen":now()}
    save(USERS_DB,users)

def add_file(name,url):
    items=get_files();ids=[]
    for x in items:
        try:ids.append(int(x.get("id",0)))
        except:pass
    x={"id":str(max(ids,default=0)+1),"name":name.strip(),"url":url.strip(),
       "downloads":0,"created_at":now(),"updated_at":now()}
    items.append(x);save(FILES_DB,items);return x

def help_text():
    return """⚡ <b>OX STORE BOT</b>

<b>File Management</b>
/upload Name | URL
/delete ID
/edit ID | New Name | New URL
/list
/stats
/clearall

<b>Locker</b>
/setkey 1 | URL
/setkey 2 | URL
/setkey 3 | URL

<b>Tools</b>
/broadcast Message
/backup
/ping
/help"""

def process(message,text):
    chat_id=message["chat"]["id"]
    cmd,_,arg=text.partition(" ")
    cmd=cmd.split("@")[0].lower();arg=arg.strip()

    if cmd in ("/start","/help"):
        send(chat_id,help_text(),keyboard());return
    if cmd=="/ping":
        send(chat_id,"🏓 <b>Pong!</b> OX Store is online.",keyboard());return
    if not is_admin(chat_id):
        send(chat_id,"⛔ <b>Admin only command.</b>");return

    if cmd=="/upload":
        p=[x.strip() for x in arg.split("|",1)]
        if len(p)!=2 or not all(p):
            send(chat_id,"❌ Use: <code>/upload Name | URL</code>");return
        x=add_file(*p)
        send(chat_id,f"✅ <b>File added</b>\n🆔 <code>{x['id']}</code>\n📦 {html.escape(x['name'])}",keyboard());return

    if cmd=="/delete":
        items=get_files();new=[x for x in items if str(x.get("id"))!=arg]
        if len(new)==len(items):send(chat_id,"❌ File ID not found.")
        else:save(FILES_DB,new);send(chat_id,"🗑️ <b>File deleted.</b>",keyboard())
        return

    if cmd=="/edit":
        p=[x.strip() for x in arg.split("|",2)]
        if len(p)!=3:
            send(chat_id,"❌ Use: <code>/edit ID | New Name | New URL</code>");return
        items=get_files();found=False
        for x in items:
            if str(x.get("id"))==p[0]:
                x["name"],x["url"],x["updated_at"]=p[1],p[2],now();found=True;break
        save(FILES_DB,items);send(chat_id,"✅ <b>Updated.</b>" if found else "❌ File not found.",keyboard());return

    if cmd=="/list":
        items=get_files()
        body="\n".join(f"🆔 <code>{x['id']}</code> • 📦 {html.escape(str(x['name']))}" for x in items)
        send(chat_id,("📋 <b>ALL FILES</b>\n\n"+body) if body else "📭 <b>No files found.</b>",keyboard());return

    if cmd=="/stats":
        items=get_files();total=sum(int(x.get("downloads",0)) for x in items)
        send(chat_id,f"📊 <b>OX STORE STATS</b>\n\n📦 Files: <b>{len(items)}</b>\n⬇️ Downloads: <b>{total}</b>\n👥 Users: <b>{len(get_users())}</b>",keyboard());return

    if cmd=="/clearall":
        send(chat_id,"⚠️ <b>Delete all files?</b>",{"inline_keyboard":[[
            {"text":"✅ YES","callback_data":"clear_yes"},
            {"text":"❌ CANCEL","callback_data":"clear_no"}]]});return

    if cmd=="/setkey":
        p=[x.strip() for x in arg.split("|",1)]
        if len(p)!=2 or p[0] not in ("1","2","3") or not p[1]:
            send(chat_id,"❌ Use: <code>/setkey 1 | URL</code>");return
        s=get_settings();s["tasks"][p[0]]=p[1];save(SETTINGS_DB,s)
        send(chat_id,f"✅ <b>Task {p[0]} updated.</b>",keyboard());return

    if cmd=="/broadcast":
        if not arg:send(chat_id,"❌ Use: <code>/broadcast Message</code>");return
        sent=0
        for uid in get_users():
            if tg("sendMessage",{"chat_id":uid,"text":html.escape(arg),"parse_mode":"HTML"}).get("ok"):sent+=1
        send(chat_id,f"📢 Broadcast finished. Delivered: <b>{sent}</b>",keyboard());return

    if cmd=="/backup":
        path=os.path.join(DATA,"oxstore_backup.json")
        with open(path,"w",encoding="utf-8") as f:
            json.dump({"files":get_files(),"users":get_users(),"settings":get_settings(),"exported_at":now()},f,ensure_ascii=False,indent=2)
        with open(path,"rb") as f:tg("sendDocument",{"chat_id":chat_id},{"document":f})
        return

    send(chat_id,"❓ Unknown command. Use /help.",keyboard())

@app.post("/webhook")
def webhook():
    supplied=request.headers.get("X-Telegram-Bot-Api-Secret-Token","")
    if WEBHOOK_SECRET and not secrets.compare_digest(supplied,WEBHOOK_SECRET):abort(403)
    update=request.get_json(silent=True) or {}
    try:
        if "callback_query" in update:
            q=update["callback_query"];chat_id=q.get("message",{}).get("chat",{}).get("id")
            tg("answerCallbackQuery",{"callback_query_id":q.get("id")})
            if q.get("data")=="clear_yes" and is_admin(chat_id):
                save(FILES_DB,[]);send(chat_id,"🗑️ <b>All files deleted.</b>",keyboard())
            elif q.get("data")=="clear_no":send(chat_id,"❎ Cancelled.",keyboard())
            return jsonify(ok=True)
        message=update.get("message")
        if not message:return jsonify(ok=True)
        register(message);text=message.get("text","").strip();chat_id=message["chat"]["id"]
        if text=="➕ Upload File":
            send(chat_id,"➕ Use: <code>/upload Name | URL</code>" if is_admin(chat_id) else "⛔ Admin only.",keyboard())
        elif text=="📊 Total Stats":process(message,"/stats")
        elif text=="📋 List All Files":process(message,"/list")
        elif text=="⚡ All Commands":send(chat_id,help_text(),keyboard())
        elif text.startswith("/"):process(message,text)
    except Exception as e:print("Webhook error:",e)
    return jsonify(ok=True)

@app.get("/set-webhook")
def set_webhook():
    if not WEBHOOK_URL:return jsonify(ok=False,error="Set WEBHOOK_URL first"),400
    return jsonify(tg("setWebhook",{"url":WEBHOOK_URL,"secret_token":WEBHOOK_SECRET,"drop_pending_updates":True}))

@app.get("/telegram-status")
def telegram_status():return jsonify(tg("getMe"))

@app.get("/api/health")
def health():return jsonify(ok=True,app="OX Store",time=now())

@app.get("/api/files")
def api_files():
    return jsonify([{"id":x["id"],"name":x["name"],"url":x["url"]} for x in get_files()])

@app.get("/api/tasks")
def api_tasks():return jsonify(get_settings()["tasks"])

@app.get("/download/<file_id>")
def download(file_id):
    items=get_files()
    for x in items:
        if str(x["id"])==str(file_id):
            x["downloads"]=int(x.get("downloads",0))+1;x["updated_at"]=now();save(FILES_DB,items)
            return redirect(x["url"])
    abort(404)

PAGE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#070a12"><title>OX Store | VIP Gaming & Cloud Hub</title>
<meta name="description" content="OX Store - VIP Gaming & Cloud Hub">
<link rel="icon" href="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png">
<style>
*{box-sizing:border-box}body{margin:0;color:#f7f9ff;font-family:Inter,system-ui,Arial;background:radial-gradient(circle at 15% 5%,#7c5cff2d,transparent 30%),radial-gradient(circle at 85% 20%,#00d4ff20,transparent 28%),#070a12}.wrap{width:min(1180px,calc(100% - 24px));margin:auto}header{position:sticky;top:0;z-index:20;background:#070a12d0;backdrop-filter:blur(18px);border-bottom:1px solid #ffffff1b}.nav{min-height:76px;display:flex;align-items:center;gap:13px}.logo{width:48px;height:48px;border-radius:50%;object-fit:cover}.brand h1{margin:0;font-size:22px;background:linear-gradient(90deg,#fff,#8e7bff,#00d4ff);-webkit-background-clip:text;color:transparent}.brand p{margin:4px 0 0;color:#aab3c7;font-size:11px}.hero{text-align:center;padding:44px 0 22px}.hero h2{font-size:clamp(30px,6vw,58px);margin:0 0 10px;letter-spacing:-2px}.hero h2 span{background:linear-gradient(90deg,#fff,#8e7bff,#00d4ff);-webkit-background-clip:text;color:transparent}.hero p{color:#aab3c7}.search{max-width:720px;margin:25px auto}.search input{width:100%;padding:17px 20px;border-radius:18px;border:1px solid #ffffff1c;background:#ffffff0d;color:white;outline:0;font-size:15px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;padding-bottom:60px}.card{padding:17px;border:1px solid #ffffff1c;border-radius:21px;background:#ffffff09;backdrop-filter:blur(14px);transition:.2s}.card:hover{transform:translateY(-4px);border-color:#8e7bff88}.badge{font-size:10px;padding:6px 9px;border-radius:20px;background:#7c5cff25;color:#c7bdff}.card h3{font-size:16px;word-break:break-word}.card p{font-size:12px;color:#aab3c7}.btn{width:100%;border:0;border-radius:13px;padding:12px;color:white;font-weight:800;background:linear-gradient(100deg,#7657ff,#00aeea);cursor:pointer}.empty{grid-column:1/-1;text-align:center;padding:45px;border:1px dashed #ffffff25;border-radius:18px;color:#aab3c7}footer{text-align:center;border-top:1px solid #ffffff1c;padding:27px;color:#8d96a9;font-size:12px}.support{position:fixed;right:16px;bottom:16px;z-index:30;width:62px;height:62px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;background:linear-gradient(145deg,#20a7ff,#6956ff);box-shadow:0 15px 40px #0008;cursor:grab;touch-action:none;user-select:none}.support span{font-size:8px;font-weight:800}.overlay{position:fixed;inset:0;z-index:50;background:#000b;backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;padding:18px}.overlay.show{display:flex}.modal{width:min(460px,100%);padding:22px;border:1px solid #ffffff1c;border-radius:25px;background:#101725}.modal h3{margin:0 0 7px}.sub{font-size:12px;color:#aab3c7}.task{display:flex;align-items:center;gap:12px;padding:13px;margin:10px 0;border:1px solid #ffffff1c;border-radius:16px;background:#ffffff08;cursor:pointer}.task.done{border-color:#20e58a88;background:#20e58a12}.icon{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;background:#7c5cff1d}.task small{display:block;color:#aab3c7;font-size:10px}.check{margin-left:auto;font-size:20px}.done .check{color:#20e58a}.actions{display:flex;gap:10px;margin-top:18px}.close{padding:12px 16px;border-radius:13px;background:#ffffff0d;color:white;border:1px solid #ffffff1c}.unlock{flex:1;opacity:.45}.unlock.ready{opacity:1}.toast{position:fixed;left:50%;bottom:25px;transform:translateX(-50%) translateY(20px);opacity:0;z-index:80;padding:12px 16px;border-radius:13px;background:#111827;border:1px solid #ffffff1c;font-size:12px;transition:.2s}.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}@media(max-width:950px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:680px){.grid{grid-template-columns:repeat(2,1fr);gap:10px}.wrap{width:calc(100% - 16px)}.logo{width:42px;height:42px}.brand h1{font-size:18px}.brand p{font-size:9px}.hero{padding:34px 0 12px}.card{padding:13px}.card h3{font-size:14px}}
</style></head><body>
<header><div class="wrap nav"><img class="logo" src="https://cdn.phototourl.com/free/2026-09-17-1b12a644-f2ad-4704-b9cf-a87edf4c49a1.png"><div class="brand"><h1>⚡ OX STORE</h1><p>OX Cloud Hub • VIP Gaming Resources & Direct Access</p></div></div></header>
<main class="wrap"><section class="hero"><h2>VIP Gaming & <span>Cloud Hub</span></h2><p>Fast access to gaming resources, cloud files and VIP downloads — all in one place.</p><div class="search"><input id="q" type="search" placeholder="Search files by name..." autocomplete="off"></div></section><section id="grid" class="grid"></section></main>
<footer>©️ 2026 @OxRehann. All rights reserved.</footer>
<div id="locker" class="overlay"><div class="modal"><h3>🔐 Unlock Download</h3><p class="sub">Complete all 3 tasks. Each button opens the required page in a new tab.</p><div id="tasks"></div><div class="actions"><button class="close" onclick="closeLocker()">Close</button><button id="unlock" class="btn unlock" disabled onclick="unlockFile()">🔒 Complete Tasks</button></div></div></div>
<div id="toast" class="toast"></div><div id="support" class="support">✈<span>Support</span></div>
<script>
const S={files:[],tasks:{},id:null,done:new Set()},$=x=>document.getElementById(x);
const esc=x=>String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
function toast(x){let e=$('toast');e.textContent=x;e.classList.add('show');clearTimeout(window.tt);window.tt=setTimeout(()=>e.classList.remove('show'),2200)}
async function load(){try{let[a,b]=await Promise.all([fetch('/api/files'),fetch('/api/tasks')]);S.files=await a.json();S.tasks=await b.json();render()}catch(e){$('grid').innerHTML='<div class="empty">Unable to load files. Please refresh.</div>'}}
function render(){let q=$('q').value.toLowerCase().trim(),a=S.files.filter(x=>String(x.name).toLowerCase().includes(q));if(!a.length){$('grid').innerHTML='<div class="empty">📭 No matching files found.</div>';return}$('grid').innerHTML=a.map(x=>'<article class="card"><span class="badge">⚡ VIP RESOURCE</span><h3>'+esc(x.name)+'</h3><p>Secure direct access • ID '+esc(x.id)+'</p><button class="btn" onclick="openLocker(\''+esc(x.id)+'\')">⬇️ Get File</button></article>').join('')}
function openLocker(id){S.id=id;S.done=new Set();drawTasks();$('locker').classList.add('show')}
function closeLocker(){$('locker').classList.remove('show')}
function drawTasks(){let a=[['1','📣','Join Telegram Channel'],['2','▶️','Subscribe YouTube'],['3','👥','Join VIP Group']];$('tasks').innerHTML=a.map(x=>'<div class="task '+(S.done.has(x[0])?'done':'')+'" onclick="completeTask(\''+x[0]+'\')"><div class="icon">'+x[1]+'</div><div><b>'+x[2]+'</b><small>Tap to open</small></div><div class="check">'+(S.done.has(x[0])?'✓':'›')+'</div></div>').join('');let u=$('unlock');u.disabled=S.done.size<3;u.classList.toggle('ready',S.done.size===3);u.textContent=S.done.size===3?'🔓 Unlock Download':'🔒 Complete Tasks'}
function completeTask(n){let u=S.tasks[n];if(!u){toast('Task URL is not configured.');return}window.open(u,'_blank','noopener,noreferrer');S.done.add(n);drawTasks()}
function unlockFile(){if(S.done.size===3&&S.id)location.href='/download/'+encodeURIComponent(S.id)}
$('q').addEventListener('input',render);$('locker').addEventListener('click',e=>{if(e.target.id==='locker')closeLocker()});load();
(function(){let e=$('support'),url=__SUPPORT__,d=false,m=false,sx=0,sy=0,ox=0,oy=0;e.addEventListener('pointerdown',x=>{d=true;m=false;sx=x.clientX;sy=x.clientY;let r=e.getBoundingClientRect();ox=r.left;oy=r.top;e.style.right='auto';e.style.bottom='auto';e.style.left=ox+'px';e.style.top=oy+'px'});window.addEventListener('pointermove',x=>{if(!d)return;if(Math.abs(x.clientX-sx)>5||Math.abs(x.clientY-sy)>5)m=true;e.style.left=Math.max(5,Math.min(innerWidth-e.offsetWidth-5,ox+x.clientX-sx))+'px';e.style.top=Math.max(5,Math.min(innerHeight-e.offsetHeight-5,oy+x.clientY-sy))+'px'});window.addEventListener('pointerup',()=>{if(!d)return;d=false;if(!m)window.open(url,'_blank','noopener,noreferrer')})})();
</script></body></html>"""
PAGE=PAGE.replace("__SUPPORT__",json.dumps(SUPPORT_URL))

@app.get("/")
def home():
    return render_template_string(PAGE)

get_files();get_users();get_settings()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=PORT,debug=False,threaded=True)

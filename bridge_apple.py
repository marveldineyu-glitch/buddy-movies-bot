import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8760379291:AAHHIOGgqTJT0IINcM4dNV2bOYDXHfV0r7I"
SESSION = "1AZWarzQBu3ZUy3OFCmSneDqRGmhmOequJNsxnU2U1n1U5gCumQo2B_7ve5en_f8KEmXMp7WUE-nWX3SnvxNuBG4xItjnz6L4rYVbZ-OhxEFX8WrF4PdGNXgWWqkgxlH9O7NEZfspmsiRd9QTE9WO0ZRhl-UcY9zXh_066TUxbsInY71vL-0GZjvHHGn1afy9Gj7nphO5h8ockeypg9Kx5bYOJ1bRki36iyrVNbUTpMfFiB4KkEAC1hFlqYoo56EEVEy7piw0TR2L3QDCZnahy3XI8Azpt0JPIc0Y5TZCDUcYyWQtkS5H_CKvnxVTIPitWadXZVHIrQRXz3Lj2KvF6ZyiYUESy0g="
SEARCH_GROUP = "@Apple_moviebot"
SEARCH_ID = 8104769075
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
button_map = {}
rate_limit = {}
pending_click = None

bot = TelegramClient('apple_bridge', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=10)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=10)
FOOTER = "\n\n❤️ @BuddyMovies_Bot"

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 600]
    for k in expired: user_sessions.pop(k, None)
    if len(button_map) > 2000:
        for k in list(button_map.keys())[:1000]: button_map.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 20: return False
    else: rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def clean_text(text):
    if not text: return "Sin descripción"
    text = text.replace("Join @F5_FILMS", "").replace("@Apple_Movies101", "")
    text = re.sub(r'https?://\S+', '', text)
    text = text.strip()
    return text if text else "Sin descripción"

def build_buttons(m):
    btns = []
    for row_idx, row in enumerate(m.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            text = (btn.text or '').strip()
            if btn.url: continue
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[data] = (m.id, row_idx, btn_idx)
                r.append(Button.inline(text[:50] if text else '📥', data))
        if r: btns.append(r)
    return btns if btns else None

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    global pending_click
    clean_memory()
    m = event.message
    if m.sender_id != SEARCH_ID: return
    
    # Archivo después de un click
    if pending_click and m.media and not m.photo:
        uid, name, reply_to = pending_click
        pending_click = None
        cap = clean_text(m.text or "") + FOOTER
        sent = await user.send_file(CANAL, m.media, caption=cap)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(GRUPO, f"🎬 **{name}**\n\n🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=reply_to)
        return
    
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    
    # Foto + botones: resultados
    if m.photo and m.buttons:
        path = await m.download_media()
        txt = clean_text(m.text)
        btns = build_buttons(m)
        await bot.send_file(GRUPO, path, caption=txt[:1000], buttons=btns, reply_to=s['reply_to'])
        try: os.unlink(path)
        except: pass

@bot.on(events.NewMessage)
async def on_user_msg(event):
    clean_memory()
    if event.is_private:
        await event.reply("🎬 <b>¡BuddyPelis!</b>\n\n📽️ <b>+5 millones de películas y series</b>\n🔍 Busca sin límites en el grupo\n\n👉 <b>Únete:</b> @BuddyMovies_official", buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]], link_preview=False)
        return
    if event.out or not event.text: return
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"): return
    if not check_rate_limit(event.sender_id):
        try: await event.reply("⏳ Espera un momento...")
        except: pass
        return
    try: s = await event.get_sender(); name = s.first_name if s else "Usuario"
    except: name = "Usuario"
    user_sessions[event.sender_id] = {'name': name, 'chat_id': event.chat_id, 'reply_to': event.message.id, 'timestamp': time.time()}
    pass  # persistente
    await user.send_message(SEARCH_GROUP, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    global pending_click
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    
    if data in button_map:
        if user_sessions:
            uid = list(user_sessions.keys())[-1]
            s = user_sessions[uid]
            pending_click = (uid, s['name'], s['reply_to'])
        info = button_map[data]
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                btn = msgs[0].buttons[info[1]][info[2]]
                await event.answer("⚡")
                await btn.click()
                return
        except: pass
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me(); clean_memory()
        except: pass

async def main():
    await user.start(); await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @Apple_moviebot Bridge → {GRUPO}")
    asyncio.create_task(heartbeat())
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()
def run_server(): HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()
threading.Thread(target=run_server, daemon=True).start()

def keep_alive():
    while True:
        time.sleep(600)
        try: urllib.request.urlopen(f"http://localhost:{int(os.environ.get('PORT', 10000))}", timeout=5)
        except: pass
threading.Thread(target=keep_alive, daemon=True).start()

asyncio.run(main())

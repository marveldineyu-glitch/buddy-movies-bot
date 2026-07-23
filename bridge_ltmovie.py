import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8808014809:AAEacf05HWO2g4HFWDTlP8IC6lXMBxILqbM"
SESSION = "1AZWarzQBu2DRpYwmFatVDHX1rQPRW4RV_mcXlR8wM72CuWSe4ydAt5zrCv_z3BIVLEgXLO95vy6sr3GsILS12Nb2yfxoeG6Fguu-scf7bQGt0uxBDwkltxztw8l66ryR_JFedA4Jzi4Jw7O892b1tRX6jZtBvHJyE93krQLZV29PhTtqEEbDrM4ua4hdUSiTuAVQb8HTgBYi2cpJyqNxXnmfHsJ-_HAa-E3ZmD2xbdikFY8CxGXzr-zMMqyB135VrAW0zNUPc_Z69huGTiiJ8Bn9Mim1TAR6gQNrhQIsDEVoOXXX9cvKHhwZcm3sqTcSb3n1-IEOqCbVceazhlCfZTFMjTiPRGg="
SEARCH_GROUP = "@Lt_Moviebot"
SEARCH_ID = 8504453537
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
search_results = {}
button_map = {}
msg_map = {}
rate_limit = {}

bot = TelegramClient('ltmovie_bridge', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

FOOTER = "\n\n➠ 𝖫𝖺𝗍𝖾𝗌𝗍 𝖴𝗉𝗅𝗈𝖺𝖽𝗌: @BuddyMovies_official\n➠ 𝖡𝗈𝗍 𝖴𝗉𝖽𝖺𝗍𝖾𝗌: @BuddyMovies_Bot"
BLOCK_URLS = ['d-3RL7TJKnVlN2Nk', 'CM_Zone', 'f9RVIwfGDYo2NDM1', 'LfvtadGw', '+d-3RL7TJKnVlN2Nk', '+f9RVIwfGDYo2NDM1']

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 300]
    for k in expired: user_sessions.pop(k, None)
    if len(search_results) > 100:
        for k in list(search_results.keys())[:50]: search_results.pop(k, None)
    if len(button_map) > 1000:
        for k in list(button_map.keys())[:500]: button_map.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 15: return False
    else: rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@FILM_PARADIZE", "@BuddyMovies_official")
    text = re.sub(r'https?://t\.me/[^\s]+', '', text)
    text = re.sub(r'https?://[^\s]*terabox[^\s]*', '', text)
    return text

def build_buttons(m):
    btns = []
    for row_idx, row in enumerate(m.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            text = (btn.text or '').strip()
            if btn.url and any(b in (btn.url or '') for b in BLOCK_URLS): continue
            if btn.url and btn.url.startswith('http') and 't.me' not in btn.url: continue
            
            if text in ['\u200b', '\u200b ']:
                ds = str(btn.data) if btn.data else ''
                if 'lang' in ds: text = '🌐'
                elif 'qual' in ds: text = '🎞️'
                elif 'nxt' in ds: text = '▶️'
                elif 'pgkb' in ds: text = '📄'
                else: text = '▫️'
            elif not text and not btn.url: continue
            
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[data] = (m.id, row_idx, btn_idx)
                r.append(Button.inline(text[:50], data))
            elif btn.url:
                r.append(Button.url(text[:50] if text else '🔗', btn.url))
        if r: btns.append(r)
    return btns if btns else None

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    if m.sender_id != SEARCH_ID: return
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    
    if m.media:
        caption = replace_ads(m.text or "") + FOOTER
        sent = await user.send_file(CANAL, m.media, caption=caption)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(GRUPO, f"🎬 **{s['name']}**\n\n🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=s['reply_to'])
    
    elif m.text and m.buttons:
        btns = build_buttons(m)
        text = replace_ads(m.text)
        sent = await bot.send_message(GRUPO, text[:4000], buttons=btns, reply_to=s['reply_to'])
        if sent: msg_map[m.id] = sent.id

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    if m.sender_id != SEARCH_ID: return
    if not m.text or not m.buttons: return
    if m.id in msg_map:
        btns = build_buttons(m)
        text = replace_ads(m.text)
        try: await bot.edit_message(GRUPO, msg_map[m.id], text[:4000], buttons=btns)
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
    button_map.clear(); msg_map.clear()
    await user.send_message(SEARCH_GROUP, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    if data in button_map:
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[button_map[data][0]])
            if msgs and msgs[0].buttons:
                btn = msgs[0].buttons[button_map[data][1]][button_map[data][2]]
                await event.answer("⚡"); await btn.click(); return
        except: pass
    try:
        msgs = await user.get_messages(SEARCH_GROUP, limit=50)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        bd = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                        if bd == data:
                            await event.answer("⚡"); await btn.click(); return
    except: pass
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me(); clean_memory()
        except: pass

async def main():
    await user.start(); await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @Lt_Moviebot Bridge → {GRUPO}")
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

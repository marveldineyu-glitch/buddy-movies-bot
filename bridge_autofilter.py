import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "7690330806:AAFAemkor12n71UAPaoJcnAcnPI_R_Xqygs"
SESSION = "1AZWarzQBu2q3JnP8YtBiwtloyr8QVF6AOFug129qO5bNQIRLsvnGelrXXIRdVYezjgm0IJNH5d_3lIBSNTxBTQnSss_Oz_MQksUSw1883Vbx5O3RyUM6UhYxhPe9jNuCHFhfTPn3iwxlQ63tJiNJ_Dd7ndNYdDFKsnrnKDvOkGX6H6UZyABCKj25nq8MCp6LRs22lV-AkmmVkdPRwL2CF7bIosmIHnfOrA2VxO_8ozC-iB08xA19YEqQtbA6YxCcYVgQuJAAyqqRIhqtHSibUloyqzYiLGUX7wWKPjYOrGOI4X-_NJAmTlkIvtQQHwd1HKI6NVLjnLker7Nas0wwUja1lOCfpQI="
SEARCH_GROUP = "@AutoFilter_Robot"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
search_results = {}
button_map = {}
rate_limit = {}

bot = TelegramClient('autofilter_prod', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

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

def cache_buttons(msg):
    if not msg or not msg.buttons: return None
    BLOCK_URLS = ['LfvtadGw', 'terabox']
    btns = []
    for row_idx, row in enumerate(msg.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            # Saltar enlaces bloqueados
            if btn.url and any(b in (btn.url or '') for b in BLOCK_URLS):
                continue
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[data] = (msg.id, row_idx, btn_idx)
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url: r.append(Button.url(btn.text[:50], btn.url))
        if r: btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@FILM_PARADIZE", "@BuddyMovies_official")
    text = text.replace("@RZXBOTZ", "@BuddyMovies_Bot")
    return text

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    if not m.sender or not m.sender.bot: return
    if m.text and any(x in m.text.lower() for x in ["save the file", "will be deleted", "select language"]): return
    
    if m.text and ("no results found" in m.text.lower() or "not available" in m.text.lower()):
        for uid, session in list(user_sessions.items()):
            try: await bot.send_message(session.get('chat_id', GRUPO), "❌ No se encontraron resultados.", reply_to=session.get('reply_to'))
            except: pass
            break
        return
    
    if m.media:
        if user_sessions:
            uid = list(user_sessions.keys())[-1]
            session = user_sessions[uid]
            name = session.get('name', 'Usuario')
            reply_to = session.get('reply_to')
            raw = replace_ads(m.text or "")
            sent = await user.send_file(CANAL, m.media, caption=raw)
            link = f"https://t.me/{CANAL[1:]}/{sent.id}"
            title = raw.split('\n')[0][:80] if raw else "Archivo"
            await bot.send_message(GRUPO, f"🎬 **{name}**\n📁 {title}\n\n🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False, reply_to=reply_to)
    
    elif m.text and len(m.text) > 20:
        buttons = cache_buttons(m)
        text = replace_ads(m.text)
        text = re.sub(r'Hey \*\*.*?\*\*!', '👋 **¡Hola!**', text)
        text = re.sub(r'Search Query:', '🔍 Búsqueda:', text)
        text = re.sub(r'Total Results:', '📊 Resultados:', text)
        text = re.sub(r'Page:', '📄 Página:', text)
        search_msg_id = m.id
        if search_msg_id in search_results:
            try: await bot.edit_message(search_results[m.id][0], search_results[m.id][1], text[:4000], buttons=buttons); return
            except: pass
        for uid, session in list(user_sessions.items()):
            try:
                sent = await bot.send_message(session.get('chat_id', GRUPO), text[:4000], buttons=buttons, reply_to=session.get('reply_to'))
                if sent: search_results[search_msg_id] = (session.get('chat_id', GRUPO), sent.id)
            except: pass
            break

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    if not m.sender or not m.sender.bot or not m.text: return
    buttons = cache_buttons(m)
    text = replace_ads(m.text)
    text = re.sub(r'Hey \*\*.*?\*\*!', '👋 **¡Hola!**', text)
    text = re.sub(r'Search Query:', '🔍 Búsqueda:', text)
    text = re.sub(r'Total Results:', '📊 Resultados:', text)
    text = re.sub(r'Page:', '📄 Página:', text)
    search_msg_id = m.id
    if search_msg_id in search_results:
        try: await bot.edit_message(search_results[m.id][0], search_results[m.id][1], text[:4000], buttons=buttons); return
        except: pass
    for uid, session in list(user_sessions.items()):
        try:
            sent = await bot.send_message(session.get('chat_id', GRUPO), text[:4000], buttons=buttons, reply_to=session.get('reply_to'))
            if sent: search_results[search_msg_id] = (session.get('chat_id', GRUPO), sent.id)
        except: pass
        break

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
    try: sender = await bot.get_entity(event.sender_id); name = sender.first_name or "Usuario"
    except: name = "Usuario"
    user_sessions[event.sender_id] = {'name': name, 'chat_id': event.chat_id, 'reply_to': event.message.id, 'timestamp': time.time()}
    button_map.clear()
    await user.send_message(SEARCH_GROUP, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    if data in button_map:
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[button_map[data][0]])
            if msgs and msgs[0].buttons:
                await event.answer("⚡")
                await msgs[0].buttons[button_map[data][1]][button_map[data][2]].click()
                return
        except: pass
    try:
        msgs = await user.get_messages(SEARCH_GROUP, limit=50)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if (btn.data.decode() if isinstance(btn.data, bytes) else btn.data) == data:
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
    print(f"✅ @AutoFilter_Bridge → {GRUPO}")
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

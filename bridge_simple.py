import asyncio, re, os, time, threading, urllib.request, gc
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8724266934:AAFZQQwhJvfkebr1csgnIKwMZKkXa44eGyA"
SESSION_READER = "1AZWarzgBu13W0EuNpoxKErbi-sroDDYq6ZWDiIaNcoKjzWrZ5J5uXknAAh-Pq7cgtT-GrhwS5rcoWmzXj5B1EsOIQsFR5qxzoJLAXUPvtEOd8eaV4BsSXyF3G8jRAPqGmbjx7FjepBwg6_TYIDUqeA6CSrkhlSIkNZ-YhTyScCvUoT_0gIQazF4KCC7jsFo1FMxQEPPgJJ3WB0QgRoHqojHEAeJ6MVxcTFmucaQKfjTkrBIlTiQdlHAJzwq7jvOd9c10TUurK0YWPgxfcCE_orEcz_CMhURbK7gJ1kSKHFx-jf3a6MGhzWclKLOkuuizGmOSJnzEkgmfIntIE_Ig3qr2qcbFgno="

SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
BOT_ID = 7537528826
FOOTER = "\n\n➠ @BuddyMovies_canal 🎬\n➠ @BuddyMovies_official 💬"

MENU_BLOCK = [
    "Hola, soy Group Search", "Si estás buscando", "Usa el comando:",
    "/search", "Hecho con cariño", "Group Search",
    "Guía de comandos", "Aquí tienes todo", "/random", "/top",
    "/stats", "/help", "¿Quieres usarme en tu grupo",
    "Toca el botón", "añadirme", "Envía /start",
    "Estadísticas generales", "Usuarios totales:", "Grupos totales:",
    "Alcance estimado:", "Búsquedas realizadas:", "Videos enviados:",
    "Videos disponibles:"
]

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
button_map = {}
msg_map = {}
rate_limit = {}

bot = TelegramClient('buddy_final_v3', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
reader = TelegramClient(StringSession(SESSION_READER), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

def clean_memory():
    now = time.time()
    for k in [k for k, v in user_sessions.items() if now - v.get('t', 0) > 600]:
        del user_sessions[k]
    if len(button_map) > 3000:
        for k in list(button_map.keys())[:1500]: del button_map[k]
    gc.collect()

def clean_text(text):
    if not text: return "Sin descripción"
    text = text.replace("@TlgramMovieGroup_Bot", "")
    text = text.replace("❤️ @TlgramMovieGroup_Bot", "")
    text = text.replace("❤️ @BuddyMovies_Bot", "")
    text = re.sub(r'https?://\\S+', '', text)
    text = re.sub(r'@(?!BuddyMovies)\\w+', '', text)
    text = text.strip()
    return text if text else "Sin descripción"
def is_menu(text):
    return any(b in text for b in MENU_BLOCK)

def cache_buttons(msg, our_msg_id=None):
    if not msg or not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = []
        for btn in row:
            if btn.data:
                if btn.text and 'inicio' in (btn.text or '').lower(): continue
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                if our_msg_id:
                    button_map[(our_msg_id, data)] = (msg.id, msg.buttons.index(row), row.index(btn))
                button_map[data] = (msg.id, msg.buttons.index(row), row.index(btn))
                r.append(Button.inline(btn.text[:50] if btn.text else '📥', data[:64]))
        if r: btns.append(r)
    return btns if btns else None

@reader.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    if m.sender_id != BOT_ID: return
    if m.text and "buscando" in m.text.lower(): return
    if m.text and is_menu(m.text): return
    
    if m.media:
        if not user_sessions: return
        uid = list(user_sessions.keys())[-1]
        s = user_sessions[uid]
        raw = clean_text(m.text or "") + FOOTER
        sent = await reader.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(GRUPO, f"🎬 **{s['name']}**\n\n🔗 {link}", 
            buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=s['rid'])

@reader.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    if m.sender_id != BOT_ID: return
    if not m.text or not m.buttons: return
    if is_menu(m.text): return
    
    text = clean_text(m.text)
    
    if m.id in msg_map:
        our_id = msg_map[m.id]
        buttons = cache_buttons(m, our_id)
        try: await bot.edit_message(GRUPO, our_id, text=text[:4000], buttons=buttons); return
        except: pass
    
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    buttons = cache_buttons(m, None)
    sent = await bot.send_message(GRUPO, text[:4000], buttons=buttons, reply_to=s['rid'])
    if sent:
        msg_map[m.id] = sent.id
        cache_buttons(m, sent.id)

@bot.on(events.NewMessage)
async def on_user(event):
    clean_memory()
    if event.is_private:
        await event.reply("🎬 <b>¡BuddyPelis!</b>\n\n📽️ <b>+5 millones de películas y series</b>\n🔍 Busca sin límites en el grupo\n\n👉 <b>Únete:</b> @BuddyMovies_official", buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]], link_preview=False)
        return
    if event.out or not event.text: return
    q = event.text.strip()
    if len(q) < 2: return
    try: name = (await event.get_sender()).first_name or "Usuario"
    except: name = "Usuario"
    user_sessions[event.sender_id] = {'name': name, 'rid': event.message.id, 't': time.time()}
    await reader.send_message(SEARCH_GROUP, f"/search {q}")

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    our_msg_id = event.message_id
    
    key = (our_msg_id, data)
    if key in button_map:
        info = button_map[key]
        try:
            msgs = await reader.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                await event.answer("⚡")
                await msgs[0].buttons[info[1]][info[2]].click()
                return
        except: pass
    
    if data in button_map:
        try:
            info = button_map[data]
            msgs = await reader.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                await event.answer("⚡")
                await msgs[0].buttons[info[1]][info[2]].click()
                return
        except: pass
    
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await reader.get_me(); clean_memory()
        except: pass

async def main():
    await reader.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @BuddyMovies_Bot → {GRUPO}")
    asyncio.create_task(heartbeat())
    await asyncio.gather(bot.run_until_disconnected(), reader.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever(), daemon=True).start()

def keep_alive():
    while True:
        time.sleep(600)
        try: urllib.request.urlopen(f"http://localhost:{int(os.environ.get('PORT', 10000))}", timeout=5)
        except: pass

threading.Thread(target=keep_alive, daemon=True).start()

asyncio.run(main())

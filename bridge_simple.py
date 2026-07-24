import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzQBu5hWbHakw_V4c82HJA0uCNxvwdS_2JHHEVUbCghWQtCFrCbvfFEAMYTh1sCL3mMpTCJMmETKHXkmgBhynikL_1MTEXJfDlFxjnZQDXf1Glbd5w0HuyCQwEP6K_F2DnAS5vsGtH452l_HDS0uQMAGryhoTV7n5Tr9-5E1DmwY4CfKNV7uzYat15FQ6Nsm_vu8iPnQEwy5w5egiY_xnULhFKIkjWrr9gm7WS_OZbSwmEThy32o3I7zxIO__BiRmAFqPnICFo8OJR_FqU7JYoGvHeScnbgbOGU-bcmFUZrq_sFBbldOn1Y4G0TBw6gLeCCUjhwIh-td7KAjaDIRdaoI_lc="
SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

MENU_BLOCK = [
    'Hola, soy Group Search', 'Si estás buscando', 'Usa el comando:',
    '/search', 'Hecho con cariño', 'Group Search',
    'Guía de comandos', 'Aquí tienes todo', '/random', '/top',
    '/stats', '/help', '¿Quieres usarme en tu grupo',
    'Toca el botón', 'añadirme', 'Envía /start',
    'Please join', 'join my', 'Updates Channel', 'try again',
    'join below', 'get file', '𝗨𝗽𝗱𝗮𝘁𝗲𝘀', 'ᴘʟᴇᴀsᴇ'
]

user_sessions = OrderedDict()
button_map = {}
msg_map = {}
rate_limit = {}

bot = TelegramClient('buddy_bot2', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=10)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=10)

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 900]
    for k in expired: user_sessions.pop(k, None)
    if len(button_map) > 3000:
        oldest = list(button_map.keys())[:1500]
        for k in oldest: button_map.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 25: return False
    else: rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def cache_buttons(msg):
    if not msg or not msg.buttons: return None
    btns = []
    for row_idx, row in enumerate(msg.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            if btn.url and ('TlgramMovieGroup_Bot' in (btn.url or '') or 'GroupSearch' in (btn.url or '')): continue
            if btn.text and any(b in (btn.text or '') for b in MENU_BLOCK): continue
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[data] = (msg.id, row_idx, btn_idx)  # Guardar para callbacks
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url:
                if any(b in (btn.text or '') for b in MENU_BLOCK): continue
                r.append(Button.url(btn.text[:50], btn.url))
        if r: btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text: return ""
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@FILM_PARADIZE", "@BuddyMovies_official")
    text = re.sub(r'@(?!BuddyMovies|BuddyNotify)\w+', '', text)
    return text

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def _debug_all(event):
    m = event.message
    print(f"DEBUG: ID={m.id} sender={m.sender_id} bot={m.sender.bot if m.sender else 'N/A'} media={bool(m.media)} text={bool(m.text)} btns={bool(m.buttons)}", flush=True)

@user.on(events.NewMessage(chats=SEARCH_GROUP))


@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    if m.sender_id != 7537528826: return
    if not m.text or not m.buttons: return
    
    text = replace_ads(m.text)
    if not text: return
    buttons = cache_buttons(m)
    # Actualizar button_map para los callbacks
    
    # Buscar si ya enviamos este mensaje al grupo
    if m.id in msg_map:
        try:
            await bot.edit_message(GRUPO, msg_map[m.id], text=text[:4000], buttons=buttons)
            return
        except: pass
    
    # Si no, enviar nuevo y guardar
    session = user_sessions.get(m.id)
    if not session and user_sessions:
        session = list(user_sessions.values())[-1]
    if session:
        sent = await bot.send_message(GRUPO, text[:4000], buttons=buttons, reply_to=session.get('reply_to'))
        if sent:
            msg_map[m.id] = sent.id
async def on_result(event):
    clean_memory()
    m = event.message
    if not m.sender: return  # Aceptar aunque no sea bot
    
    if m.text:
        pass  # No bloquear
        low = m.text.lower()
        if any(x in low for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    
    if m.media:
        # Si es un archivo, guardar en canal
        if not m.photo and m.document:
            caption = replace_ads(m.text or "")
            if caption:
                sent = await user.send_file(CANAL, m.media, caption=caption)
                link = f"https://t.me/{CANAL[1:]}/{sent.id}"
                session = user_sessions.get(m.id)
                if not session and user_sessions:
                    session = list(user_sessions.values())[-1]
                if session:
                    await bot.send_message(GRUPO, f"🎬 **{session['name']}**

🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=session.get('reply_to'))
            return
        
        # Buscar por m.id primero, luego último
        session = user_sessions.get(m.id)
        if not session and user_sessions:
            # Tomar el último que hizo búsqueda
            session = list(user_sessions.values())[-1]
        if session:
            print(f"DEBUG: Enviando media a {session['name']}", flush=True)
            raw = replace_ads(m.text or "")
            if not raw: return
            sent = await user.send_file(CANAL, m.media, caption=raw)
            link = f"https://t.me/{CANAL[1:]}/{sent.id}"
            title = raw.split('\n')[0][:80] if raw else "Archivo"
            await bot.send_message(GRUPO, f"🎬 **{session['name']}**\n📁 {title}\n\n🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False, reply_to=session.get('reply_to'))
    
    elif m.text and m.buttons and len(m.text) > 20:
        text = replace_ads(m.text)
        if not text: return
        buttons = cache_buttons(m)
        session = user_sessions.get(m.id)
        if not session and user_sessions:
            session = list(user_sessions.values())[-1]
        if session:
            print(f"DEBUG: Enviando texto a {session['name']}", flush=True)
            await bot.send_message(GRUPO, text[:4000], buttons=buttons, reply_to=session.get('reply_to'))

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
    sent = await user.send_message(SEARCH_GROUP, f"/search {q}")
    user_sessions[sent.id] = {'user_id': event.sender_id, 'name': name, 'chat_id': event.chat_id, 'reply_to': event.message.id, 'timestamp': time.time()}

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
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me(); clean_memory()
        except: pass

async def main():
    await user.start(); await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @BuddyMovies_Bot → {GRUPO}")
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

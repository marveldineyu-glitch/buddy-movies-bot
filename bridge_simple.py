import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ CONFIG ============
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzQBu5hWbHakw_V4c82HJA0uCNxvwdS_2JHHEVUbCghWQtCFrCbvfFEAMYTh1sCL3mMpTCJMmETKHXkmgBhynikL_1MTEXJfDlFxjnZQDXf1Glbd5w0HuyCQwEP6K_F2DnAS5vsGtH452l_HDS0uQMAGryhoTV7n5Tr9-5E1DmwY4CfKNV7uzYat15FQ6Nsm_vu8iPnQEwy5w5egiY_xnULhFKIkjWrr9gm7WS_OZbSwmEThy32o3I7zxIO__BiRmAFqPnICFo8OJR_FqU7JYoGvHeScnbgbOGU-bcmFUZrq_sFBbldOn1Y4G0TBw6gLeCCUjhwIh-td7KAjaDIRdaoI_lc="
SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

# ============ ESTADO OPTIMIZADO ============
user_sessions = OrderedDict()  # {user_id: {name, reply_to, timestamp}}
search_results = {}  # {search_msg_id: (chat_id, result_msg_id)} - para editar el correcto
button_map = {}  # {callback_data: (search_msg_id, row_idx, btn_idx)} - RESPUESTA INSTANTÁNEA
rate_limit = {}

bot = TelegramClient('buddy_bot2', API_ID, API_HASH, 
                     retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=15)

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 300]
    for k in expired:
        user_sessions.pop(k, None)
    if len(search_results) > 100:
        oldest = list(search_results.keys())[:50]
        for k in oldest:
            search_results.pop(k, None)
    if len(button_map) > 1000:
        oldest = list(button_map.keys())[:500]
        for k in oldest:
            button_map.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 15:
            return False
    else:
        rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def cache_buttons(msg):
    """Guarda botones en caché para respuesta instantánea"""
    if not msg or not msg.buttons:
        return None
    btns = []
    for row_idx, row in enumerate(msg.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                # Guardar en caché: data -> (msg_id, row, col)
                button_map[data] = (msg.id, row_idx, btn_idx)
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url:
                r.append(Button.url(btn.text[:50], btn.url))
        if r:
            btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@FILM_PARADIZE", "@BuddyMovies_official")
    text = text.replace("@RZXBOTZ", "@BuddyMovies_Bot")
    return text

# ============ RESULTADOS ============
@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot:
        return
    
    if m.text:
        low = m.text.lower()
        if any(x in low for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]):
            return
    
    if m.media:
        # Buscar usuario con búsqueda activa más reciente
        if user_sessions:
            uid = list(user_sessions.keys())[-1]
            session = user_sessions[uid]
            name = session.get('name', 'Usuario')
            reply_to = session.get('reply_to')
            
            raw = replace_ads(m.text or "")
            sent = await user.send_file(CANAL, m.media, caption=raw)
            link = f"https://t.me/{CANAL[1:]}/{sent.id}"
            title = raw.split('\n')[0][:80] if raw else "Archivo"
            
            await bot.send_message(
                GRUPO,
                f"🎬 **{name}**\n📁 {title}\n\n🔗 {link}",
                buttons=[[Button.url("🎥 VER CONTENIDO", link)]],
                link_preview=False,
                reply_to=reply_to
            )
    
    # También manejar resultados de texto (paginación)
    elif m.text and m.buttons and len(m.text) > 20:
        buttons = cache_buttons(m)
        text = replace_ads(m.text)
        search_msg_id = m.id
        
        # Ver si ya existe un mensaje para este search_msg_id
        if search_msg_id in search_results:
            chat_id, result_msg_id = search_results[search_msg_id]
            try:
                await bot.edit_message(chat_id, result_msg_id, text[:4000], buttons=buttons)
                return
            except:
                pass
        
        # Enviar nuevo
        for uid, session in list(user_sessions.items()):
            try:
                sent = await bot.send_message(
                    session.get('chat_id', GRUPO),
                    text[:4000],
                    buttons=buttons,
                    reply_to=session.get('reply_to')
                )
                if sent:
                    search_results[search_msg_id] = (session.get('chat_id', GRUPO), sent.id)
            except:
                pass
            break

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot or not m.text:
        return
    
    low = m.text.lower()
    if any(x in low for x in ["buscando", "espera"]):
        return
    
    # Cachear botones
    buttons = cache_buttons(m)
    text = replace_ads(m.text)
    
    # EDITAR el mensaje correcto usando search_msg_id
    search_msg_id = m.id
    if search_msg_id in search_results:
        chat_id, result_msg_id = search_results[search_msg_id]
        try:
            await bot.edit_message(chat_id, result_msg_id, text[:4000], buttons=buttons)
            return
        except:
            pass
    
    # Si no existe, enviar nuevo al último usuario
    for uid, session in list(user_sessions.items()):
        try:
            sent = await bot.send_message(
                session.get('chat_id', GRUPO),
                text[:4000],
                buttons=buttons,
                reply_to=session.get('reply_to')
            )
            if sent:
                search_results[search_msg_id] = (session.get('chat_id', GRUPO), sent.id)
        except:
            pass
        break

# ============ USUARIOS ============
@bot.on(events.NewMessage)
async def on_user_msg(event):
    clean_memory()
    
    # PV: redirigir
    if event.is_private:
        await event.reply(
            "🎬 <b>¡BuddyPelis!</b>\n\n"
            "📽️ <b>+5 millones de películas y series</b>\n"
            "🔍 Busca sin límites en el grupo\n\n"
            "👉 <b>Únete:</b> @BuddyMovies_official",
            buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]],
            link_preview=False
        )
        return
    
    if event.out or not event.text:
        return
    
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"):
        return
    
    user_id = event.sender_id
    
    if not check_rate_limit(user_id):
        try:
            await event.reply("⏳ Espera un momento...")
        except:
            pass
        return
    
    try:
        sender = await bot.get_entity(user_id)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    
    # Guardar sesión del usuario
    user_sessions[user_id] = {
        'name': name,
        'chat_id': event.chat_id,
        'reply_to': event.message.id,
        'timestamp': time.time()
    }
    
    # Limpiar botones viejos de este usuario
    button_map.clear()
    
    # Enviar búsqueda y guardar referencia
    sent = await user.send_message(SEARCH_GROUP, f"/search {q}")
    user_sessions[user_id]['search_msg_id'] = sent.id

# ============ CALLBACKS INSTANTÁNEOS ============
@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data:
        return
    
    # RESPUESTA INSTANTÁNEA desde caché
    if data in button_map:
        msg_id, row_idx, btn_idx = button_map[data]
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[msg_id])
            if msgs and msgs[0].buttons:
                btn = msgs[0].buttons[row_idx][btn_idx]
                await event.answer("⚡")
                await btn.click()
                return
        except:
            pass
    
    # Fallback: buscar en mensajes recientes
    try:
        msgs = await user.get_messages(SEARCH_GROUP, limit=50)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        btn_data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                        if btn_data == data:
                            await event.answer("⚡")
                            await btn.click()
                            return
    except:
        pass
    
    await event.answer("⏳ Expiró")

# ============ ARRANQUE ============
async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try:
            await bot.get_me()
            await user.get_me()
            clean_memory()
        except:
            pass

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Bridge listo → {GRUPO}")
    asyncio.create_task(heartbeat())
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()

def run_server():
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    url = f"http://localhost:{port}"
    while True:
        time.sleep(600)
        try:
            urllib.request.urlopen(url, timeout=5)
        except:
            pass

threading.Thread(target=keep_alive, daemon=True).start()

asyncio.run(main())

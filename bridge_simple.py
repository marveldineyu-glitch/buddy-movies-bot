import asyncio, os, threading, gc, time
from collections import deque, OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ CONFIG ============
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "7812301734:AAHIXx70G83tb41pBczdCcdhHRiBlz43g7A"
SESSION = "1AZWarzYBu72KHN1Z6-0Q0I9KI7JSZ_3dpMTSuiN6aNsb_STMDHX10-fo09zyXAOhbRSHE0gJJlFU3iRYuqPMAu_U_ka8RuHU98KFxMVTOGWZrilLGBsZSUirNT1C4-8Q4Po3XX_kWI_6GSCEc_pRBgCktyuzZL4rSXwKlCSpx1-NmSqQ-Vb62e47hKUznQugDB31Sl71tM7-3MLMp3EmqbIA_m5f6zA2gZYX4swtE0aCw1Su8neeah5rGTQI7imOISQZRNgStTrmcmBtmUVVPmzqM6-b512Np3cLBv5vIMBchTwqB77ipLEj-xHhdB8hdIPPJtvo9aqQBtZv_faUy-PrhAeiNmo="
SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@mabu205"
MAX_MEMORY_MB = 250  # Límite auto-limpieza
MAX_QUEUE_PER_USER = 3  # Máximo búsquedas por usuario
SESSION_TTL = 120  # Segundos para expirar sesiones

# ============ ESTADO ============
os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

# Cola FIFO con límite
search_queue = deque(maxlen=200)
# Sesiones: {request_id: {chat_id, user_id, name, reply_to, timestamp}}
user_sessions = OrderedDict()
# Mirror para ediciones: {search_msg_id: (our_msg_id, chat_id)}
mirror = OrderedDict()
# Rate limit: {user_id: [timestamps]}
rate_limit = {}

bot = TelegramClient('simple_bot', API_ID, API_HASH, 
                     retry_delay=3, auto_reconnect=True, timeout=20)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=20)

# ============ UTILIDADES ============
def clean_memory():
    """Limpia memoria agresivamente"""
    now = time.time()
    
    # Limpiar sesiones expiradas
    expired = [k for k, v in user_sessions.items() if now - v['timestamp'] > SESSION_TTL]
    for k in expired:
        user_sessions.pop(k, None)
    
    # Limpiar mirror viejos
    if len(mirror) > 100:
        oldest = list(mirror.keys())[:50]
        for k in oldest:
            mirror.pop(k, None)
    
    # Limpiar rate limit viejos
    expired_rl = [k for k, v in rate_limit.items() if now - v[0] > 60]
    for k in expired_rl:
        rate_limit.pop(k, None)
    
    # Forzar garbage collection
    gc.collect()
    
    # Verificar memoria
    try:
        import psutil
        mem = psutil.Process().memory_info().rss / 1024 / 1024
        if mem > MAX_MEMORY_MB:
            print(f"⚠️ Memoria alta: {mem:.0f}MB - Limpiando...")
            user_sessions.clear()
            mirror.clear()
            rate_limit.clear()
            gc.collect()
    except:
        pass

def check_rate_limit(user_id):
    """Verifica si el usuario puede hacer búsqueda"""
    now = time.time()
    if user_id in rate_limit:
        timestamps = rate_limit[user_id]
        # Mantener solo últimos 60 segundos
        recent = [t for t in timestamps if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 10:  # Máximo 10 búsquedas por minuto
            return False
    else:
        rate_limit[user_id] = []
    
    rate_limit[user_id].append(now)
    return True

def make_buttons(msg):
    """Convierte botones de Telethon a formato Telegram"""
    if not msg or not msg.buttons:
        return None
    btns = []
    for row in msg.buttons:
        r = []
        for btn in row:
            if btn.data:
                r.append(Button.inline(btn.text[:50], btn.data[:64]))
            elif btn.url:
                r.append(Button.url(btn.text[:50], btn.url))
        if r:
            btns.append(r)
    return btns if btns else None

# ============ MANEJADORES ============
@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    """Recibe resultados del bot de búsqueda"""
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot:
        return
    
    # Ignorar mensajes de estado
    if m.text:
        low = m.text.lower()
        if any(x in low for x in ["buscando", "espera", "recuerda", "ayúdanos", "compártelo", "gracias"]):
            return
    
    # Procesar siguiente en cola
    if m.media and search_queue:
        try:
            request_id = search_queue.popleft()
            session = user_sessions.pop(request_id, None)
            
            if session:
                raw = m.text or ""
                sent = await user.send_file(CANAL, m.media, caption=raw)
                link = f"https://t.me/{CANAL[1:]}/{sent.id}"
                title = raw.split('\n')[0][:80] if raw else "Archivo"
                
                await bot.send_message(
                    session['chat_id'],
                    f"🎬 **{session['name']}**\n📁 {title}\n\n🔗 {link}",
                    buttons=[[Button.url("🎥 VER CONTENIDO", link)]],
                    link_preview=False,
                    reply_to=session.get('reply_to')
                )
        except Exception as e:
            print(f"Error enviando media: {e}")

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    """Maneja ediciones del bot de búsqueda"""
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot or not m.text:
        return
    
    low = m.text.lower()
    if any(x in low for x in ["buscando", "espera", "recuerda", "ayúdanos", "compártelo", "gracias"]):
        return
    
    # Buscar en mirror
    if m.id in mirror:
        our_id, chat_id = mirror[m.id]
        try:
            buttons = make_buttons(m)
            await bot.edit_message(
                chat_id, our_id,
                m.text[:4000],
                buttons=buttons
            )
            return
        except:
            pass
    
    # Buscar en sesiones activas
    for req_id, session in list(user_sessions.items()):
        if session.get('search_msg_id') == m.id:
            try:
                sent = await bot.send_message(
                    session['chat_id'],
                    m.text[:4000],
                    buttons=make_buttons(m)
                )
                if sent:
                    mirror[m.id] = (sent.id, session['chat_id'])
            except:
                pass
            break

@bot.on(events.NewMessage)
async def on_msg(event):
    """Recibe mensajes de usuarios"""
    clean_memory()
    
    if event.out or not event.text:
        return
    
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"):
        return
    
    user_id = event.sender_id
    chat_id = event.chat_id
    
    # Rate limit
    if not check_rate_limit(user_id):
        try:
            await event.reply("⏳ Demasiadas búsquedas. Espera un momento.")
        except:
            pass
        return
    
    # Obtener nombre
    try:
        sender = await bot.get_entity(user_id)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    
    # Enviar búsqueda
    try:
        sent = await user.send_message(SEARCH_GROUP, f"/search {q}")
        
        # Guardar sesión
        user_sessions[sent.id] = {
            'chat_id': chat_id,
            'user_id': user_id,
            'name': name,
            'reply_to': event.message.id,
            'search_msg_id': sent.id,
            'timestamp': time.time()
        }
        search_queue.append(sent.id)
        
    except Exception as e:
        print(f"Error búsqueda: {e}")

@bot.on(events.CallbackQuery)
async def on_click(event):
    """Maneja clicks en botones"""
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data:
        return
    
    # Buscar en mensajes recientes del grupo de búsqueda
    try:
        msgs = await user.get_messages(SEARCH_GROUP, limit=20)
        for m in msgs:
            if m.sender and m.sender.bot and m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if btn.data == data:
                            await event.answer("⚡ Enviando...")
                            await btn.click()
                            return
    except:
        pass
    
    await event.answer("⏳ Búsqueda expirada. Intenta de nuevo.")

# ============ ARRANQUE ============
async def heartbeat():
    """Mantiene viva la conexión"""
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
    print(f"✅ Bridge optimizado listo")
    print(f"📊 Memoria máx: {MAX_MEMORY_MB}MB")
    print(f"👥 Cola FIFO: {MAX_QUEUE_PER_USER} búsquedas/usuario")
    
    asyncio.create_task(heartbeat())
    await asyncio.gather(
        bot.run_until_disconnected(),
        user.run_until_disconnected()
    )

# Servidor HTTP para Render
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), H).serve_forever()

threading.Thread(target=run_server, daemon=True).start()

asyncio.run(main())

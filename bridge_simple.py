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
GRUPO = "@mabu205"  # GRUPO FIJO

# ============ ESTADO ============
os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

search_queue = deque(maxlen=200)
user_sessions = OrderedDict()
mirror = OrderedDict()
rate_limit = {}

bot = TelegramClient('simple_bot', API_ID, API_HASH, 
                     retry_delay=3, auto_reconnect=True, timeout=20)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=20)

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 120]
    for k in expired:
        user_sessions.pop(k, None)
    if len(mirror) > 100:
        oldest = list(mirror.keys())[:50]
        for k in oldest:
            mirror.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 10:
            return False
    else:
        rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def make_buttons(msg):
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

# ============ RESULTADOS -> SIEMPRE AL GRUPO ============
@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot:
        return
    
    if m.text:
        low = m.text.lower()
        if any(x in low for x in ["buscando", "espera", "recuerda", "ayúdanos", "compártelo", "gracias"]):
            return
    
    if m.media and search_queue:
        try:
            request_id = search_queue.popleft()
            session = user_sessions.pop(request_id, {})
            name = session.get('name', 'Usuario')
            reply_to = session.get('reply_to')
            
            raw = m.text or ""
            sent = await user.send_file(CANAL, m.media, caption=raw)
            link = f"https://t.me/{CANAL[1:]}/{sent.id}"
            title = raw.split('\n')[0][:80] if raw else "Archivo"
            
            # SIEMPRE ENVIAR AL GRUPO
            await bot.send_message(
                GRUPO,  # <-- GRUPO FIJO
                f"🎬 **{name}**\n📁 {title}\n\n🔗 {link}",
                buttons=[[Button.url("🎥 VER CONTENIDO", link)]],
                link_preview=False,
                reply_to=reply_to
            )
            print(f"✅ Enviado a {GRUPO} para {name}")
        except Exception as e:
            print(f"❌ Error: {e}")

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot or not m.text:
        return
    
    low = m.text.lower()
    if any(x in low for x in ["buscando", "espera"]):
        return
    
    # Intentar editar en mirror
    if m.id in mirror:
        our_id, _ = mirror[m.id]
        try:
            await bot.edit_message(
                GRUPO, our_id,  # <-- GRUPO FIJO
                m.text[:4000],
                buttons=make_buttons(m)
            )
            print(f"✅ Editado en {GRUPO}")
            return
        except Exception as e:
            print(f"❌ Error edit: {e}")
    
    # Si no está en mirror, enviar nuevo al GRUPO
    try:
        sent = await bot.send_message(
            GRUPO,  # <-- GRUPO FIJO
            m.text[:4000],
            buttons=make_buttons(m)
        )
        if sent:
            mirror[m.id] = (sent.id, GRUPO)
        print(f"✅ Nuevo mensaje en {GRUPO}")
    except Exception as e:
        print(f"❌ Error: {e}")

# ============ RECIBIR BÚSQUEDAS ============
@bot.on(events.NewMessage)
async def on_msg(event):
    clean_memory()
    
    if event.out or not event.text:
        return
    
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"):
        return
    
    user_id = event.sender_id
    
    # Rate limit
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
    
    try:
        sent = await user.send_message(SEARCH_GROUP, f"/search {q}")
        user_sessions[sent.id] = {
            'name': name,
            'reply_to': event.message.id,
            'timestamp': time.time()
        }
        search_queue.append(sent.id)
        print(f"🔍 {name}: {q}")
    except Exception as e:
        print(f"❌ Error búsqueda: {e}")

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data:
        return
    
    try:
        msgs = await user.get_messages(SEARCH_GROUP, limit=20)
        for m in msgs:
            if m.sender and m.sender.bot and m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if btn.data == data:
                            await event.answer("⚡")
                            await btn.click()
                            return
    except:
        pass
    
    await event.answer("⏳ Expiró. Busca de nuevo.")

# ============ ARRANQUE ============
async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try:
            await bot.get_me()
            await user.get_me()
            clean_memory()
            print(f"💓 Heartbeat - Sesiones: {len(user_sessions)}")
        except:
            pass

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Bridge listo -> {GRUPO}")
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
asyncio.run(main())

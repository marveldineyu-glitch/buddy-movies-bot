import asyncio, re, os, threading, gc, time, urllib.request
from collections import deque, OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8463069047:AAGeZg0IQd-1-Mv3ubxqnwZY1oJgxio9hr8"
SESSION = "1AZWarzQBuzncKy_mbzKcjlq0_XeKVuhMaiHWMBs3kkt9hmss9EcHTh9f9RtgQYkoDx4oXfLs8rnlwzNA8AHxmt47X2J3r4YJr0QVNVzX3meQKnDv1EKsnctVofcPlsHGuXPZutTrhs0-rtMFXO8TYMESuLbcu0BlENZDA6LVWzItTe17yMvgWexGLJMIyhO-yIrRxHr4838YkKxdxUflsSkjtSZIV8W4EWtrd6eOcTcZbaQyJEUT6jcyXrePbmfaOjMoOsx1PJF1dQisoPP_C-mRSHgp59Za4LmBM4EqQgzXeoPdUdXFRDkCJAfjzc3p6lnU7HqEtcKmm2EIzY43vj_iKSroOOo="
SEARCH_BOT = "@TlgramMovieSearch_Bot"
CANAL = "@prueba22299"
GRUPO = "@mabu205"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

search_queue = deque(maxlen=200)
user_sessions = OrderedDict()
our_msgs = {}
rate_limit = {}

bot = TelegramClient('search_bridge', API_ID, API_HASH, 
                     retry_delay=3, auto_reconnect=True, timeout=20)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=20)

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 300]
    for k in expired:
        user_sessions.pop(k, None)
    if len(our_msgs) > 50:
        oldest = list(our_msgs.keys())[:25]
        for k in oldest:
            our_msgs.pop(k, None)
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
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url:
                r.append(Button.url(btn.text[:50], btn.url))
        if r:
            btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text:
        return text
    text = re.sub(r'@\w+MovieGroup\w*', '@mabu205', text)
    text = re.sub(r'@\w+MovieSearch\w*', '@MotorBusquedaBot', text)
    return text

# ============ RECIBIR RESPUESTAS DEL BOT ============
@user.on(events.NewMessage(chats=SEARCH_BOT))
async def on_search_response(event):
    clean_memory()
    m = event.message
    
    if not m.sender or not m.sender.bot:
        return
    
    if not search_queue:
        return
    
    # Peek sin hacer pop
    request_id = search_queue[0]
    session = user_sessions.get(request_id, {})
    if not session:
        return
    
    user_id = session.get('user_id')
    name = session.get('name', 'Usuario')
    reply_to = session.get('reply_to')
    
    # ¿Es un mensaje FINAL? (tiene media o botones de acción)
    es_final = bool(m.media) or (m.buttons and len(m.buttons) > 0 and not any(
        'método' in (btn.text or '').lower() for row in m.buttons for btn in row
    ))
    
    if es_final:
        # Hacer pop solo cuando es el mensaje final
        search_queue.popleft()
        user_sessions.pop(request_id, None)
    
    # Enviar SIEMPRE el mensaje al grupo (incluso los intermedios)
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (m.text or "Archivo").split('\n')[0][:80]
        await bot.send_message(
            GRUPO,
            f"🎬 **{name}**\n📁 {title}\n\n🔗 {link}",
            buttons=[[Button.url("🎥 VER CONTENIDO", link)]],
            link_preview=False,
            reply_to=reply_to
        )
    elif m.text:
        txt = replace_ads(m.text)
        buttons = make_buttons(m)
        
        # SIEMPRE editar si ya existe un mensaje, o crear nuevo
        if user_id in our_msgs:
            try:
                await bot.edit_message(GRUPO, our_msgs[user_id], txt[:4000], buttons=buttons)
                return
            except:
                # Si falla la edición, eliminar referencia y crear nuevo
                our_msgs.pop(user_id, None)
        
        # Solo crear mensaje nuevo si no existe uno previo
        sent = await bot.send_message(GRUPO, txt[:4000], buttons=buttons, reply_to=reply_to)
        if sent:
            our_msgs[user_id] = sent.id

# ============ RECIBIR BÚSQUEDAS ============
@bot.on(events.NewMessage)
async def on_user_msg(event):
    clean_memory()
    
    if event.is_private:
        await event.reply(
            "🎬 <b>¡Motor de Búsqueda!</b>\n\n"
            "📽️ <b>Películas y series</b>\n"
            "🔍 Busca sin límites en el grupo\n\n"
            "👉 <b>Únete:</b> @mabu205",
            buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/mabu205")]],
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
    
    try:
        our_msgs.pop(user_id, None)
        sent = await user.send_message(SEARCH_BOT, q)
        user_sessions[sent.id] = {
            'user_id': user_id,
            'name': name,
            'reply_to': event.message.id,
            'timestamp': time.time()
        }
        search_queue.append(sent.id)
    except Exception as e:
        print(f"❌ Error: {e}")

# ============ CALLBACKS ============
@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data:
        return
    
    # Buscar en mensajes recientes del chat del bot
    try:
        msgs = await user.get_messages(SEARCH_BOT, limit=50)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        btn_data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                        if btn_data == data:
                            await event.answer("⚡")
                            await btn.click()
                            return
        print(f"⚠️ Botón no encontrado: {data[:30]}")
    except Exception as e:
        print(f"❌ Error click: {e}")
    
    await event.answer("⏳ Búsqueda expirada.")

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

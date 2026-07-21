import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ CONFIG ============
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8463069047:AAGeZg0IQd-1-Mv3ubxqnwZY1oJgxio9hr8"
SESSION = "1AZWarzQBuzncKy_mbzKcjlq0_XeKVuhMaiHWMBs3kkt9hmss9EcHTh9f9RtgQYkoDx4oXfLs8rnlwzNA8AHxmt47X2J3r4YJr0QVNVzX3meQKnDv1EKsnctVofcPlsHGuXPZutTrhs0-rtMFXO8TYMESuLbcu0BlENZDA6LVWzItTe17yMvgWexGLJMIyhO-yIrRxHr4838YkKxdxUflsSkjtSZIV8W4EWtrd6eOcTcZbaQyJEUT6jcyXrePbmfaOjMoOsx1PJF1dQisoPP_C-mRSHgp59Za4LmBM4EqQgzXeoPdUdXFRDkCJAfjzc3p6lnU7HqEtcKmm2EIzY43vj_iKSroOOo="
SEARCH_BOT = "@TlgramMovieSearch_Bot"
CANAL = "@prueba22299"
GRUPO = "@mabu205"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

active = OrderedDict()
our_msg = {}
mirror3 = {}
button_map = {}
rate_limit = {}

bot = TelegramClient('search_bridge2', API_ID, API_HASH,
                     retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=15)

def clean_memory():
    now = time.time()
    expired = [k for k, v in active.items() if now - v.get('timestamp', 0) > 300]
    for k in expired:
        active.pop(k, None)
        our_msg.pop(k, None)
    if len(mirror3) > 100:
        oldest = list(mirror3.keys())[:50]
        for k in oldest:
            mirror3.pop(k, None)
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
    if not msg or not msg.buttons: return None
    btns = []
    for row_idx, row in enumerate(msg.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[data] = (msg.id, row_idx, btn_idx)
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url:
                r.append(Button.url(btn.text[:50], btn.url))
        if r: btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieSearch_Bot", "@BuddyNotify_Bot")
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@MotorBusquedaBot", "@BuddyNotify_Bot")
    text = text.replace("Estrenos 2026", "@BuddyMovies_official")
    text = text.replace("@FILM_PARADIZE", "@BuddyMovies_official")
    text = text.replace("@RZXBOTZ", "@BuddyMovies_Bot")
    return text

def get_user():
    if not active: return None, None, "Usuario"
    valid = [k for k in active if k is not None]
    if not valid: return None, None, "Usuario"
    uid = valid[-1]
    return uid, active[uid]['chat'], active[uid]['name']

# ============ BOT 3: @TlgramMovieSearch_Bot ============
@user.on(events.NewMessage(chats=SEARCH_BOT))
async def on_bot3(event):
    clean_memory()
    m = event.message
    uid, chat_id, name = get_user()
    if not uid: return
    
    if m.text:
        low = m.text.lower()
        if any(x in low for x in ["maldito", "comparte", "terabox", "revisa el anuncio", "no te lo guardes", "procesando", "espera un momento"]):
            return
    
    if m.media:
        print(f"📁 ARCHIVO RECIBIDO: {m.text[:80] if m.text else 'Sin texto'}")
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        print(f"📤 Enviado a canal: {sent.id}")
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (m.text or "Archivo").split('\n')[0][:80]
        await bot.send_message(
            chat_id,
            f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**\n\n🔗 {link}",
            buttons=[[Button.url("🎥 VER CONTENIDO", link)]],
            link_preview=False
        )
        return
    
    if not m.text: return
    
    txt = replace_ads(m.text)
    buttons = cache_buttons(m)
    
    # EDITAR mensaje existente
    if uid in our_msg:
        try:
            await bot.edit_message(chat_id, our_msg[uid], txt[:4000], buttons=buttons)
            mirror3[m.id] = our_msg[uid]
            return
        except:
            pass
    
    # Enviar nuevo
    sent = await bot.send_message(chat_id, txt[:4000], buttons=buttons)
    our_msg[uid] = sent.id
    mirror3[m.id] = sent.id

@user.on(events.MessageEdited(chats=SEARCH_BOT))
async def on_bot3_edit(event):
    clean_memory()
    m = event.message
    if not m.text: return
    if any(x in m.text.lower() for x in ["procesando", "espera un momento"]): return
    if m.id in mirror3:
        uid, chat_id, name = get_user()
        if uid:
            try:
                await bot.edit_message(chat_id, mirror3[m.id], replace_ads(m.text)[:4000], buttons=cache_buttons(m))
            except: pass

# ============ USUARIOS ============
@bot.on(events.NewMessage)
async def on_user(event):
    clean_memory()
    
    if event.is_private:
        await event.reply(
            "🎬 <b>¡BuddyPelis!</b>\n\n"
            "📽️ <b>Películas y series</b>\n"
            "🔍 Busca sin límites en el grupo\n\n"
            "👉 <b>Únete:</b> @BuddyMovies_official",
            buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]],
            link_preview=False
        )
        return
    
    if event.out: return
    q = event.text.strip() if event.text else ""
    if len(q) < 2 or q.startswith("/"): return
    
    uid = event.sender_id or event.chat_id
    
    if not check_rate_limit(uid):
        try:
            await event.reply("⏳ Espera un momento...")
        except:
            pass
        return
    
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    
    active[uid] = {'chat': event.chat_id, 'name': name, 'timestamp': time.time()}
    mirror3.clear()
    our_msg.pop(uid, None)
    button_map.clear()
    await user.send_message(SEARCH_BOT, q)

# ============ CALLBACKS INSTANTÁNEOS ============
@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    
    if data in button_map:
        msg_id, row_idx, btn_idx = button_map[data]
        try:
            msgs = await user.get_messages(SEARCH_BOT, ids=[msg_id])
            if msgs and msgs[0].buttons:
                btn = msgs[0].buttons[row_idx][btn_idx]
                await event.answer("⚡")
                await btn.click()
                return
        except:
            pass
    
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
    print(f"✅ Bridge @TlgramMovieSearch_Bot → {GRUPO}")
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

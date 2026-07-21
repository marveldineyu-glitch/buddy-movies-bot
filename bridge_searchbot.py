import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
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

active = {}
our_msg = {}
mirror3 = {}

bot = TelegramClient('search_bridge', API_ID, API_HASH,
                     retry_delay=3, auto_reconnect=True, timeout=20)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
                      retry_delay=3, auto_reconnect=True, timeout=20)

def get_user():
    if not active: return None, None, "Usuario"
    valid = [k for k in active if k is not None]
    if not valid: return None, None, "Usuario"
    uid = valid[-1]
    return uid, active[uid]['chat'], active[uid]['name']

def make_buttons(msg):
    if not msg or not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = []
        for btn in row:
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                r.append(Button.inline(btn.text[:50], data[:64]))
            elif btn.url:
                r.append(Button.url(btn.text[:50], btn.url))
        if r: btns.append(r)
    return btns if btns else None

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieSearch_Bot", "@MotorBusquedaBot")
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    return text

# ============ BOT 3: @TlgramMovieSearch_Bot (LÓGICA PROBADA) ============
@user.on(events.NewMessage(chats=SEARCH_BOT))
async def on_bot3(event):
    m = event.message
    uid, chat_id, name = get_user()
    if not uid: return
    
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (m.text or "Archivo").split('\n')[0]
        await bot.send_message(GRUPO, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False)
        return
    
    if not m.text: return
    if any(x in m.text.lower() for x in ["maldito", "comparte", "terabox", "revisa el anuncio", "no te lo guardes", "procesando", "espera un momento"]): return
    
    txt = replace_ads(m.text)
    if uid in our_msg:
        try:
            await bot.edit_message(chat_id, our_msg[uid], txt[:4000], buttons=make_buttons(m))
            mirror3[m.id] = our_msg[uid]
            return
        except:
            pass
    
    sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
    our_msg[uid] = sent.id
    mirror3[m.id] = sent.id

@user.on(events.MessageEdited(chats=SEARCH_BOT))
async def on_bot3_edit(event):
    m = event.message
    if not m.text: return
    if any(x in m.text.lower() for x in ["procesando", "espera un momento"]): return
    if m.id in mirror3:
        uid, chat_id, name = get_user()
        if uid:
            try:
                await bot.edit_message(chat_id, mirror3[m.id], replace_ads(m.text)[:4000], buttons=make_buttons(m))
            except: pass

# ============ USUARIOS ============
@bot.on(events.NewMessage)
async def on_user(event):
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
    
    if event.out: return
    q = event.text.strip() if event.text else ""
    if len(q) < 2 or q.startswith("/"): return
    
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    
    active[uid] = {'chat': event.chat_id, 'name': name}
    mirror3.clear()
    our_msg.pop(uid, None)
    await user.send_message(SEARCH_BOT, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    active[uid] = {'chat': event.chat_id, 'name': name}
    
    # Buscar en el chat del bot
    msgs = await user.get_messages(SEARCH_BOT, limit=20)
    for m in msgs:
        if m.buttons:
            for row in m.buttons:
                for btn in row:
                    btn_data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                    if btn_data == data:
                        await event.answer("⚡")
                        await btn.click()
                        return
    await event.answer("⏳ Expiró")

# ============ ARRANQUE ============
async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try:
            await bot.get_me()
            await user.get_me()
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

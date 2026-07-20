import asyncio, re, gc, os, threading, socket, sys
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ BLOQUEO ANTI-DUPLICADO ============
lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    lock_socket.bind(("0.0.0.0", 9999))
except OSError:
    print("❌ Otra instancia ya está corriendo. Saliendo...")
    sys.exit(0)

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzUBuywXWSwew2UbNZ9AUDrHRL0DgKX1cW4N-RnWZP3mRg-bAVbsYvtkTUaQ55KEMgWUBeLdkudNjgulUaanm4CZ0Jvsm6wjOO5PneFJ50rhUB6JOXAbPa8Iv9cnLtj8i9wIkx-GQG3za7GNqpCIMnMmgB9-DtfTg6H8iXdnoyUr3Xux0lIaJGTwxntJ1vaH3dx8w-k-b1gPI6Dwsr_nHnMA3nDxViRrX5221WYKGIVqOKxSceBYL9opDXsjf1h1ncDPwUOHTjI-nUChL8E9p6k8ZSgPwewa_B1tLKUf3SxgQrYUSBG6I66SF_4NV4IgvQkyhMCJAvRCjPRh2ZhfS9SokRU="
SEARCH_GROUP2 = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
GRUPO_ID = 2311102965
ADMIN_ID = 7771137226

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(10000, 100, 100)

bot = TelegramClient('buddy_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
active = {}
mirror2 = {}
mirror_chat = {}

def make_buttons(msg):
    if not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = [Button.inline(btn.text, btn.data) if btn.data else Button.url(btn.text, btn.url) for btn in row]
        btns.append(r)
    return btns

def get_user():
    if not active: return None, None, "Usuario"
    valid = [k for k in active if k is not None]
    if not valid: return None, None, "Usuario"
    uid = valid[-1]
    return uid, active[uid]['chat'], active[uid]['name']

@user.on(events.NewMessage(chats=SEARCH_GROUP2))
async def on_bot2_new(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.media:
        raw = (m.text or "").replace('@TlgramMovieGroup_Bot', '@BuddyMovies_official')
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (raw.split('\n')[0] if raw else "Archivo")[:100]
        reply_to = active[uid].get('reply_to') if uid in active else None
        await bot.send_message(chat_id, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False, reply_to=reply_to)

@user.on(events.MessageEdited(chats=SEARCH_GROUP2))
async def on_bot2_edit(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    if not m.text: return
    if any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.id in mirror2:
        try:
            await bot.edit_message(mirror_chat[m.id], mirror2[m.id], m.text[:4000].replace('@TlgramMovieGroup_Bot', '@BuddyMovies_official'), buttons=make_buttons(m))
            return
        except: pass
    uid, chat_id, name = get_user()
    if uid and "Resultados" in m.text:
        sent = await bot.send_message(chat_id, m.text[:4000].replace('@TlgramMovieGroup_Bot', '@BuddyMovies_official'), buttons=make_buttons(m))
        mirror2[m.id] = sent.id
        mirror_chat[m.id] = chat_id

@bot.on(events.NewMessage)
async def on_user(event):
    if event.out: return
    if event.is_private and event.sender_id != ADMIN_ID:
        await event.reply(f"👋 ¡Hola!\n\nSolo funciono en el grupo:\n👉 {GRUPO}")
        return
    q = event.text.strip() if event.text else ""
    if len(q) < 2 or q.startswith("/"): return
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    active[uid] = {'chat': event.chat_id, 'name': name, 'reply_to': event.message.id}
    await user.send_message(SEARCH_GROUP2, f"/search {q}")

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data
    if not data: return
    uid = event.sender_id or event.chat_id
    active[uid] = {'chat': event.chat_id, 'name': (await event.get_sender()).first_name or "Usuario"}
    msgs = await user.get_messages(SEARCH_GROUP2, limit=10)
    for m in msgs:
        if m.sender and m.sender.bot and m.buttons:
            for row in m.buttons:
                for btn in row:
                    if btn.data == data:
                        await event.answer("⚡")
                        await btn.click()
                        return
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(300)
        try: await bot.get_me()
        except: pass
        gc.collect()

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Bot listo - {GRUPO}")
    asyncio.create_task(heartbeat())
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
def s():
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()
threading.Thread(target=s, daemon=True).start()

asyncio.run(main())

import asyncio, re, gc, os, threading
from collections import deque
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzkBu14FNj4w0ZhJiodVvjAWJGVSlCgaM8tbwae7x6xavyHD61MU5J58NOvGUjrcQWnJm_ZO8VeUsdilrHMPaxH3V8U8h3vHq1x8Ti6FMAsvaglbYKK49pZ5gC79AzMK6bP0HpYWMU5QkJuAGKQ_Pe69Ox6oI6db5YQ2eKp_ZxPLSXn6VrkYgItcr3ZxlcQgGVqXmoa0qbt_xqiHN2EG8ZQCLv-Quy2p9NPCsoThUpAaj5dxYh7GAInQL2UujlrgkBfH_IHHYUNVpEboYv_1pe34S2uAS5GoHsEX5r6zTIjQb-E6nzmzMimexxAFdOFdQzFj1ct4eC6rTuid9-lJb_Dlhc8="
SEARCH_GROUP2 = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
GRUPO_ID = 2311102965
ADMIN_ID = 7771137226

os.environ['PYTHONOPTIMIZE'] = '2'
search_queue = deque()
user_sessions = {}

bot = TelegramClient('buddy_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

def make_buttons(msg):
    if not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = [Button.inline(btn.text, btn.data) if btn.data else Button.url(btn.text, btn.url) for btn in row]
        btns.append(r)
    return btns

@user.on(events.NewMessage(chats=SEARCH_GROUP2))
async def on_bot2_new(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.media:
        if search_queue:
            request_id = search_queue.popleft()
            session = user_sessions.pop(request_id, None)
            if session:
                raw = (m.text or "").replace('@TlgramMovieGroup_Bot', '@BuddyMovies_official')
                sent = await user.send_file(CANAL, m.media, caption=raw)
                link = f"https://t.me/{CANAL[1:]}/{sent.id}"
                title = (raw.split('\n')[0] if raw else "Archivo")[:100]
                await bot.send_message(GRUPO, f"🎬 **Aquí tienes {session['name']}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False, reply_to=session['reply_to'])

@user.on(events.MessageEdited(chats=SEARCH_GROUP2))
async def on_bot2_edit(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    if not m.text: return
    if any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    for request_id, session in list(user_sessions.items()):
        if session.get('search_msg_id') == m.id:
            try:
                await bot.edit_message(GRUPO, session['result_msg_id'], m.text[:4000].replace('@TlgramMovieGroup_Bot', '@BuddyMovies_official'), buttons=make_buttons(m))
            except: pass
            break

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
    sent_msg = await user.send_message(SEARCH_GROUP2, f"/search {q}")
    user_sessions[sent_msg.id] = {'chat': GRUPO, 'name': name, 'reply_to': event.message.id, 'search_msg_id': sent_msg.id}
    search_queue.append(sent_msg.id)
    if len(user_sessions) > 100:
        oldest = list(user_sessions.keys())[:50]
        for k in oldest: user_sessions.pop(k, None)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data
    if not data: return
    try:
        sender = await event.get_sender()
        name = sender.first_name or "Usuario"
    except: name = "Usuario"
    msgs = await user.get_messages(SEARCH_GROUP2, limit=20)
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

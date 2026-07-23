import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8894814453:AAGAuF3cjETqYt_mY2os9raZgMxSZtFqD_E"
SESSION = "1AZWarzQBuw2Qy79iGpD5cWK5pf1LtqHo8f-gjYTl7G8c4wcEvAXuhRifBWgMyrQeXsW62Jpv2YbE3yQJJC1D520D4CPbkOHM5c9NUlDOaQNGDg4gbTzf00Ye6KlbLifZpgQI9Zk3SO9EeMJlq7MVvqUNUgMpCaxYl3oMcAhhqnzHPgMmdQR9epRSKMU6d_PeQ7NHThlpYHHYB5wpMBz2-IaajdMMXPB4-shgmIHGeh_BdQy6UArhkcLFaxCu-f60MK39MUzYq4UElN0aaSn7HuSfaszh5QlALJQe9AZrP1Jsa7UzErtsZ0JDsoMt6ujcvgpXCYu3xYQkNTQh1s7n-qb4y8uaQZU="
SEARCH_GROUP = "@Angela2_moviebot"
SEARCH_ID = 8143714699
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
button_map = {}
msg_map = {}
rate_limit = {}

bot = TelegramClient('angela_bridge', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
FOOTER = "\n\n➠ 𝖫𝖺𝗍𝖾𝗌𝗍 𝖴𝗉𝗅𝗈𝖺𝖽𝗌: @BuddyMovies_official\n➠ 𝖡𝗈𝗍 𝖴𝗉𝖽𝖺𝗍𝖾𝗌: @BuddyMovies_Bot"

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 300]
    for k in expired: user_sessions.pop(k, None)
    if len(button_map) > 2000:
        for k in list(button_map.keys())[:1000]: button_map.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 15: return False
    else: rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

def replace_ads(text):
    if not text: return text
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'.*Updates\s*:.*', '', text)
    text = re.sub(r'.*auto.delete.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'.*copyright.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

def build_buttons(m, our_msg_id):
    btns = []
    for row_idx, row in enumerate(m.buttons):
        r = []
        for btn_idx, btn in enumerate(row):
            text = (btn.text or '').strip()
            
            if btn.url and 'start=' in btn.url:
                parsed = urlparse(btn.url)
                params = parse_qs(parsed.query)
                start_data = params.get('start', [''])[0]
                if start_data:
                    fake_data = f"dl_{start_data[:40]}"
                    button_map[(our_msg_id, fake_data)] = (m.id, row_idx, btn_idx, start_data)
                    r.append(Button.inline(text[:50] if text else '📥', fake_data))
                continue
            
            if btn.url: continue
            
            if btn.data:
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                button_map[(our_msg_id, data)] = (m.id, row_idx, btn_idx, None)
                if text in ['\u200b', '\u200b ']:
                    ds = str(btn.data)
                    if 'lang' in ds: text = '🌐'
                    elif 'qual' in ds: text = '🎞️'
                    elif 'next' in ds: text = '▶️'
                    elif 'buttons' in ds: text = '📄'
                    else: text = '▫️'
                r.append(Button.inline(text[:50], data))
        if r: btns.append(r)
    return btns if btns else None

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    clean_memory()
    m = event.message
    if m.sender_id != SEARCH_ID: return
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    
    if m.media:
        caption = replace_ads(m.text or "") + FOOTER
        sent = await user.send_file(CANAL, m.media, caption=caption)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(GRUPO, f"🎬 **{s['name']}**\n\n🔗 {link}", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=s['reply_to'])
    
    elif m.text and m.buttons:
        sent = await bot.send_message(GRUPO, "...", reply_to=s['reply_to'])
        our_id = sent.id
        btns = build_buttons(m, our_id)
        text = replace_ads(m.text)
        await bot.edit_message(GRUPO, our_id, text[:4000], buttons=btns)
        msg_map[m.id] = our_id

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    clean_memory()
    m = event.message
    if m.sender_id != SEARCH_ID: return
    if not m.text or not m.buttons: return
    if m.id in msg_map:
        our_id = msg_map[m.id]
        btns = build_buttons(m, our_id)
        text = replace_ads(m.text)
        try: await bot.edit_message(GRUPO, our_id, text[:4000], buttons=btns)
        except: pass

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
    try: s = await event.get_sender(); name = s.first_name if s else "Usuario"
    except: name = "Usuario"
    user_sessions[event.sender_id] = {'name': name, 'chat_id': event.chat_id, 'reply_to': event.message.id, 'timestamp': time.time()}
    await user.send_message(SEARCH_GROUP, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    our_msg_id = event.message_id
    key = (our_msg_id, data)
    
    if key in button_map:
        info = button_map[key]
        start_param = info[3] if len(info) > 3 else None
        if start_param:
            await event.answer("⚡ Solicitando...")
            await user.send_message(SEARCH_GROUP, f"/start {start_param}")
            return
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                btn = msgs[0].buttons[info[1]][info[2]]
                await event.answer("⚡"); await btn.click(); return
        except: pass
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me(); clean_memory()
        except: pass

async def main():
    await user.start(); await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @Angela2_moviebot Bridge → {GRUPO}")
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

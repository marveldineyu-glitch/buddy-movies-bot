import asyncio, re, os, time, threading, urllib.request, gc
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8463069047:AAGeZg0IQd-1-Mv3ubxqnwZY1oJgxio9hr8"
SESSION = "1AZWarzoBuxH7fOsG6u9PfDFhZlh7Q9GBPC0ArDGeZLxm8ZBkCu_KVw-7FkEoiDg57Nz_hwupWu35td7OvVDXR3giYHrvFjBzWtdq6Dh3CqACzDc1M2VjufyMX3c0DaER8f_UVBV5uUYokBdcRfNNCwOwZQ6Ebf6njGe4bJmNQtCkKT6CO37Pbl0ON_80sxP1Ijhv9EA1IGjpkfe2mVYFZ24KJAdGDHFcReM71Q3JTsOzWXBXdNwhnY8WmjNeWYG0b8hkYhjp5hXa5PS-uF_Qb5oFDDp5CU9o-CjRU3quuwE1nUK2DKx4QlVlKjppg0hgsYFwz7OVyB_ldyz3pVvVBmKvorCFW_M="
SEARCH_GROUP = "@TlgramMovieSearch_Bot"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
BOT_ID = 7266628580
FOOTER = "\n\n➠ @BuddyMovies_canal 🎬\n➠ @BuddyMovies_official 💬"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
button_map = {}
msg_map = {}

bot = TelegramClient('notify_bridge', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

def clean_text(text):
    if not text: return "..."
    # Eliminar líneas específicas
    text = re.sub(r'🔗.*Estrenos 2026.*', '', text)
    text = re.sub(r'🔗.*@\w+.*', '', text)
    # Eliminar @menciones
    text = text.replace("@TlgramMovieSearch_Bot", "")
    text = text.replace("@BuddyNotify_Bot", "")
    text = re.sub(r'@\w+', '', text)
    # Eliminar enlaces
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\[Estrenos 2026\]\(.*?\)', '', text)
    # Eliminar líneas vacías múltiples
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip() or "..."

def cache_buttons(msg, our_msg_id=None):
    if not msg or not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = []
        for btn in row:
            if btn.data:
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']):
                    continue
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']): continue
                data = btn.data.decode() if isinstance(btn.data, bytes) else btn.data
                if our_msg_id: button_map[(our_msg_id, data)] = (msg.id, msg.buttons.index(row), row.index(btn))
                button_map[data] = (msg.id, msg.buttons.index(row), row.index(btn))
                r.append(Button.inline(btn.text[:50] if btn.text else '📥', data[:64]))
        if r: btns.append(r)
    return btns if btns else None

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    m = event.message
    if m.sender_id != BOT_ID: return
    
    if m.buttons and "selecciona un método" in (m.text or "").lower():
        for row in m.buttons:
            for btn in row:
                if btn.data and "text" in str(btn.data).lower():
                    await btn.click()
                    return
    
    if m.buttons and "selecciona un almacén" in (m.text or "").lower():
        for row in m.buttons:
            for btn in row:
                if btn.data:
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']): continue
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']): continue
                    await btn.click()
                    return
    
    if m.media:
        if not user_sessions: return
        uid = list(user_sessions.keys())[-1]
        s = user_sessions[uid]
        raw = clean_text(m.text or "") + FOOTER
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(GRUPO, f"🎬 **{s['name']}**\n\n🔗 {link}", 
            buttons=[[Button.url("🎥 VER CONTENIDO", link)]], reply_to=s['rid'])
        return
    
    if not m.buttons: return
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    text = clean_text(m.text)
    buttons = cache_buttons(m, None)
    sent = await bot.send_message(GRUPO, text[:4000], buttons=buttons, reply_to=s['rid'])
    if sent:
        msg_map[m.id] = sent.id
        cache_buttons(m, sent.id)

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    m = event.message
    if m.sender_id != BOT_ID: return
    if not m.text or not m.buttons: return
    
    if "selecciona un almacén" in (m.text or "").lower():
        for row in m.buttons:
            for btn in row:
                if btn.data:
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']): continue
                if btn.text and any(s in (btn.text or '').lower() for s in ['inicio', 'menú principal', 'menu principal']): continue
                    await btn.click()
                    return
    
    text = clean_text(m.text)
    if m.id in msg_map:
        our_id = msg_map[m.id]
        buttons = cache_buttons(m, our_id)
        try: await bot.edit_message(GRUPO, our_id, text=text[:4000], buttons=buttons); return
        except: pass
    
    if not user_sessions: return
    uid = list(user_sessions.keys())[-1]
    s = user_sessions[uid]
    buttons = cache_buttons(m, None)
    sent = await bot.send_message(GRUPO, text[:4000], buttons=buttons, reply_to=s['rid'])
    if sent:
        msg_map[m.id] = sent.id
        cache_buttons(m, sent.id)

@bot.on(events.NewMessage)
async def on_user(event):
    if event.is_private:
        await event.reply("🎬 <b>¡BuddyPelis!</b>\n\n📽️ <b>+5 millones de películas y series</b>\n🔍 Busca sin límites en el grupo\n\n👉 <b>Únete:</b> @BuddyMovies_official", buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]], link_preview=False)
        return
    if event.out or not event.text: return
    q = event.text.strip()
    if len(q) < 2: return
    try: name = (await event.get_sender()).first_name or "Usuario"
    except: name = "Usuario"
    user_sessions[event.sender_id] = {'name': name, 'rid': event.message.id, 't': time.time()}
    await user.send_message(SEARCH_GROUP, q)

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data.decode() if isinstance(event.data, bytes) else event.data
    if not data: return
    our_msg_id = event.message_id
    key = (our_msg_id, data)
    if key in button_map:
        info = button_map[key]
        try:
            msgs = await user.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                await event.answer("⚡"); await msgs[0].buttons[info[1]][info[2]].click(); return
        except: pass
    if data in button_map:
        try:
            info = button_map[data]
            msgs = await user.get_messages(SEARCH_GROUP, ids=[info[0]])
            if msgs and msgs[0].buttons:
                await event.answer("⚡"); await msgs[0].buttons[info[1]][info[2]].click(); return
        except: pass
    await event.answer("⏳ Expiró")

async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me()
        except: pass

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ @BuddyNotify_Bot → {GRUPO}")
    asyncio.create_task(heartbeat())
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
threading.Thread(target=lambda: HTTPServer(("0.0.0.0", int(os.environ.get("PORT",10000))), H).serve_forever(), daemon=True).start()
def ka():
    while True:
        time.sleep(600)
        try: urllib.request.urlopen(f"http://localhost:{int(os.environ.get('PORT',10000))}", timeout=5)
        except: pass
threading.Thread(target=ka, daemon=True).start()
asyncio.run(main())

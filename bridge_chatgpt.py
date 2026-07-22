import asyncio, os, threading, gc, time, urllib.request
from collections import OrderedDict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8876362915:AAGEkzWdokk2rjc0j3w-iOTdT5lIdDjjPYs"
SESSION = "1AZWarzsBu3ny9-HTgWpuIkTxb2vRDvQJu0tU-l_79zEFPRsg1fX4vV7aQw5Qew3KyFIi7-VuZDR3niQvGaXRh89KP2AywppMfdolEwgquZIRROPPNuLQovcl5hpp4vvt6r1gb6Zr1EZrOBOp4PKiG2RLff0b2bKWzRPd-pr5CbDPtTrIBSFMXnMCDwZvs8wxB6n1KZ6H6b5Ndunvr3yOhSKDfzqhWq8Rz3HpGq6iWo1vI418VFHbUXVvlGBe47jEDQc6eaosxAv1EFjRVbmumdQT7aF1GW3u-H_pfpRwpYQHb0r3hVBMCva6eDuTZ_L5rOaE2Zix41Z3C51umX6FZjdHGuyed20="
CHATGPT_BOT = "@ChatGPT_rgbot"
GRUPO = "@mabu205"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

user_sessions = OrderedDict()
rate_limit = {}

bot = TelegramClient('chatgpt_bridge', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

def clean_memory():
    now = time.time()
    expired = [k for k, v in user_sessions.items() if now - v.get('timestamp', 0) > 300]
    for k in expired: user_sessions.pop(k, None)
    gc.collect()

def check_rate_limit(user_id):
    now = time.time()
    if user_id in rate_limit:
        recent = [t for t in rate_limit[user_id] if now - t < 60]
        rate_limit[user_id] = recent
        if len(recent) >= 10: return False
    else: rate_limit[user_id] = []
    rate_limit[user_id].append(now)
    return True

# ============ RECIBIR RESPUESTAS DE CHATGPT ============
@user.on(events.NewMessage(chats=CHATGPT_BOT))
async def on_chatgpt_response(event):
    clean_memory()
    m = event.message
    
    print(f"DEBUG ChatGPT: text={bool(m.text)}, media={bool(m.media)}", flush=True)
    if not m.sender or not m.sender.bot: return
    
    # Ignorar mensajes de estado
    if m.text and any(x in m.text.lower() for x in ["typing", "thinking", "generating"]): return
    
    if user_sessions:
        uid = list(user_sessions.keys())[-1]
        session = user_sessions[uid]
        name = session.get('name', 'Usuario')
        reply_to = session.get('reply_to')
        
        if m.text:
            await bot.send_message(
                GRUPO,
                f"🤖 **ChatGPT responde a {name}:**\n\n{m.text[:4000]}",
                reply_to=reply_to
            )
        elif m.media:
            await bot.send_message(
                GRUPO,
                f"🤖 **ChatGPT envió un archivo a {name}:**",
                reply_to=reply_to
            )
            await bot.send_file(GRUPO, m.media, reply_to=reply_to)

# ============ RECIBIR PREGUNTAS DE USUARIOS ============
@bot.on(events.NewMessage)
async def on_user_msg(event):
    clean_memory()
    
    if event.is_private:
        await event.reply(
            "🤖 <b>ChatGPT Bot</b>\n\n"
            "💬 Haz tus preguntas en el grupo\n\n"
            f"👉 <b>Únete:</b> {GRUPO}",
            buttons=[[Button.url("🎥 IR AL GRUPO", f"https://t.me/{GRUPO[1:]}")]],
            link_preview=False
        )
        return
    
    if event.out or not event.text: return
    
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"): return
    
    user_id = event.sender_id
    
    if not check_rate_limit(user_id):
        try: await event.reply("⏳ Espera un momento...")
        except: pass
        return
    
    try: sender = await bot.get_entity(user_id); name = sender.first_name or "Usuario"
    except: name = "Usuario"
    
    user_sessions[user_id] = {
        'name': name,
        'chat_id': event.chat_id,
        'reply_to': event.message.id,
        'timestamp': time.time()
    }
    
    # Enviar pregunta a ChatGPT
    await user.send_message(CHATGPT_BOT, q)

# ============ ARRANQUE ============
async def heartbeat():
    while True:
        await asyncio.sleep(180)
        try: await bot.get_me(); await user.get_me(); clean_memory()
        except: pass

async def main():
    await user.start(); await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ ChatGPT Bridge → {GRUPO}")
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

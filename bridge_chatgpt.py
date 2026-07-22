import asyncio, re, os, threading, gc, time, urllib.request
from collections import OrderedDict, deque
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8952066629:AAHLnoIl62kY0wf4XrFWKiiDq9UaNbjk9zE"
SESSION = "1AZWarzsBu3ny9-HTgWpuIkTxb2vRDvQJu0tU-l_79zEFPRsg1fX4vV7aQw5Qew3KyFIi7-VuZDR3niQvGaXRh89KP2AywppMfdolEwgquZIRROPPNuLQovcl5hpp4vvt6r1gb6Zr1EZrOBOp4PKiG2RLff0b2bKWzRPd-pr5CbDPtTrIBSFMXnMCDwZvs8wxB6n1KZ6H6b5Ndunvr3yOhSKDfzqhWq8Rz3HpGq6iWo1vI418VFHbUXVvlGBe47jEDQc6eaosxAv1EFjRVbmumdQT7aF1GW3u-H_pfpRwpYQHb0r3hVBMCva6eDuTZ_L5rOaE2Zix41Z3C51umX6FZjdHGuyed20="
CHATBOT = "@gpt3ru_chat_bot"
CHATBOT_ID = 6157862059
GRUPO = "@BuddyMovies_official"

os.environ['PYTHONOPTIMIZE'] = '2'
gc.set_threshold(5000, 50, 50)

question_queue = deque()
rate_limit = {}

bot = TelegramClient('chatgpt_final', API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH, retry_delay=3, auto_reconnect=True, timeout=15)

def clean_memory():
    now = time.time()
    if len(question_queue) > 100:
        for _ in range(50): question_queue.popleft()
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

def clean_response(text):
    text = re.sub(r'https?://\S+', '', text)
    cut_patterns = [
        r'\n\nSi quieres[,:]?\s*puedo:?',
        r'\n\n¿Qué prefieres\?',
        r'\n\n¿Te gustaría\?',
        r'\n\n¿Quieres\?',
        r'\n\nPuedo\s+',
        r'\n\nDime\s+',
        r'\n\nSi necesitas\s+',
        r'\n\nEspero que\s+',
    ]
    for pattern in cut_patterns:
        text = re.split(pattern, text, flags=re.IGNORECASE)[0]
    return text.strip()

@user.on(events.NewMessage(chats=CHATBOT))
async def on_response(event):
    clean_memory()
    m = event.message
    if m.sender_id != CHATBOT_ID: return
    if m.text and "please wait" in m.text.lower(): return
    
    if question_queue and m.text:
        uid, name, reply_to = question_queue.popleft()
        clean = clean_response(m.text)
        try:
            await bot.send_message(GRUPO, f"🤖 **GPT para {name}:**\n\n{clean[:2000]}", reply_to=reply_to)
        except:
            await bot.send_message(GRUPO, f"🤖 **GPT para {name}:**\n\n{clean[:2000]}")

@bot.on(events.NewMessage)
async def on_user_msg(event):
    clean_memory()
    
    if event.is_private:
        await event.reply("🤖 <b>ChatGPT Bot</b>\n\n💬 Haz tus preguntas en el grupo\n\n👉 <b>Únete:</b> @BuddyMovies_official", buttons=[[Button.url("🎥 IR AL GRUPO", "https://t.me/BuddyMovies_official")]], link_preview=False)
        return
    
    if event.out or not event.text: return
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"): return
    
    uid = event.sender_id
    
    if not check_rate_limit(uid):
        try: await event.reply("⏳ Espera un momento...")
        except: pass
        return
    
    try:
        s = await event.get_sender()
        name = s.first_name if s else "Usuario"
    except:
        name = "Usuario"
    
    await event.reply(f"⏳ **{name}**, estoy consultando a ChatGPT...")
    question_queue.append((uid, name, event.message.id))
    
    formatted_q = f"Hola soy {name}. Quiero saber sobre esto: '{q}'. ¿Qué es exactamente? ¿Es una película, serie, anime, novela, libro, videojuego, canción o qué tipo de contenido es? Dame una respuesta clara y directa, sin ofrecer ayuda adicional."
    await user.send_message(CHATBOT, formatted_q)

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

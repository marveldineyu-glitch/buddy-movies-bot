import asyncio, pickle, json, os, re, hashlib, threading
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8463069047:AAGeZg0IQd-1-Mv3ubxqnwZY1oJgxio9hr8"
SESSION = "1AZWarzgBu7T0qCqBvsZnNQmCPiU-8vdteMOcKuPBC14WtUC7pT3QuAG55Y6GtlbkZZ8XN_KDugD214Jqe-XExmoCW-FJdoO-c0PIDpEnLXYM61XRIpMh-WolwbhREweQY0FeGVuR2PfpnSEMOqlwb3wUC3lRxS6zGV-QzwxmiB_cpXVpDoSn61poZTcevExy_ao5cKVV5Zzjc9QF7uEhaRhCiDbENWUoZOQGqMDG5iT9PdbUf_Hd9tYElcb4jXjegsTDH-baufMF00Rxqp2_GQvGLk7Tq8DZqnugeB0hzZHrLNTqPrH5V0lJURcJS-yswbganim5kTTG5auZG9TnllbT6iM5Mv8="
ADMIN_ID = 7771137226
INDEX_FILE = "video_index_render.pkl"
CANALES_FILE = "canales_render.json"

content_index = defaultdict(list)
title_index = {}
canales = []

if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, 'rb') as f:
        data = pickle.load(f)
        content_index = defaultdict(list, data.get('content_index', {}))
        title_index = data.get('title_index', {})
if os.path.exists(CANALES_FILE):
    with open(CANALES_FILE) as f: canales = json.load(f)

def guardar():
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump({'content_index': dict(content_index), 'title_index': title_index}, f)
    with open(CANALES_FILE, 'w') as f: json.dump(canales, f)

def limpiar(text):
    if not text: return "Sin título"
    text = re.sub(r'https?://\S+', '', text)
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 10: return line[:200]
    return text.strip()[:200] or "Sin título"

async def indexar(canal):
    try:
        ent = await user.get_entity(canal)
        count = 0
        async for m in user.iter_messages(ent, limit=None):
            if m.media and m.text:
                ct = limpiar(m.text)
                words = re.findall(r'\b\w+\b', ct.lower())
                md = {'canal': canal, 'titulo': ct, 'msg_id': m.id}
                for k in set(w for w in words if len(w) > 2):
                    content_index[k].append(md)
                title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
                count += 1
                if count % 5000 == 0:
                    guardar()
                    try: await bot.send_message(ADMIN_ID, f"📊 {canal}: {count}")
                    except: pass
        if canal not in canales: canales.append(canal)
        guardar()
        await bot.send_message(ADMIN_ID, f"✅ {canal}: {count} | 📊 Total: {len(title_index)}")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"❌ {canal}: {e}")

async def main():
    global bot, user
    bot = TelegramClient('render_bot', API_ID, API_HASH)
    user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    
    @bot.on(events.NewMessage(pattern='/addchannel'))
    async def addchannel(event):
        if event.sender_id != ADMIN_ID: return
        texto = event.text.replace('/addchannel', '').strip()
        nuevos = re.findall(r'@\w+', texto)
        if not nuevos:
            await event.reply("❌ /addchannel @canal")
            return
        await event.reply(f"⏳ {len(nuevos)} canales en segundo plano...")
        for c in nuevos:
            if c not in canales:
                asyncio.create_task(indexar(c))
            else:
                await event.reply(f"⚠️ {c} ya indexado")
    
    @bot.on(events.NewMessage(pattern='/total'))
    async def total(event):
        await event.reply(f"📊 {len(title_index)} títulos | 📁 {len(canales)} canales")
    
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    await bot.send_message(ADMIN_ID, f"🚀 Indexador Render listo\n📊 {len(title_index)} títulos")
    await bot.run_until_disconnected()

# Servidor falso
class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()
def s(): HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()
threading.Thread(target=s, daemon=True).start()

asyncio.run(main())

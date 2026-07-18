import asyncio, pickle, json, os, re, time, hashlib
from collections import defaultdict
from telethon import TelegramClient
from telethon.sessions import StringSession

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
        print(f"📂 Cargados {len(title_index)} títulos")

if os.path.exists(CANALES_FILE):
    with open(CANALES_FILE) as f:
        canales = json.load(f)

def guardar():
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump({'content_index': dict(content_index), 'title_index': title_index}, f)
    with open(CANALES_FILE, 'w') as f:
        json.dump(canales, f)

async def enviar(msg):
    try:
        await bot.send_message(ADMIN_ID, msg)
    except:
        pass

def limpiar(text):
    if not text: return "Sin título"
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    for line in text.split('\n'):
        line = line.strip()
        if len(line) > 10:
            return line[:200]
    return text.strip()[:200] or "Sin título"

async def indexar(canal):
    try:
        ent = await user.get_entity(canal)
        count = 0
        async for m in user.iter_messages(ent, limit=2000):
            if m.media and m.text:
                ct = limpiar(m.text)
                words = re.findall(r'\b\w+\b', ct.lower())
                kw = [w for w in words if len(w) > 2]
                md = {'canal': canal, 'titulo': ct, 'msg_id': m.id}
                for k in set(kw):
                    content_index[k].append(md)
                title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
                count += 1
                if count % 500 == 0:
                    guardar()
        
        if canal not in canales:
            canales.append(canal)
        guardar()
        await enviar(f"✅ {canal}: {count}")
        return count
    except Exception as e:
        await enviar(f"❌ {canal}: {e}")
        return 0

bot = TelegramClient('render_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

PENDIENTES = [
    "@CineMaxService", "@PokemonDPSubEsp", "@pelis_series_anime_1209", "@kdramasflanes", "@doramasestrenos",
    "@DoramasGratiskDramaLovers", "@uno_mas_2033", "@Korean_doramas_top", "@doramasesptg",
    "@animesdetodoslosgeneros", "@peliculasdebarbie1", "@barbiepeliculass", "@barbieepeliculaspqsiixx",
    "@peliskun", "@pelisanimeymas", "@GRUPPETE_DE_PELICULA_ANIME_Y_MAS", "@the_Legend_Of_Tomiris_Movie",
    "@chicanosforever", "@pelisjokerHDelpapa", "@lanoviadeltitan", "@escatologiafilmesmovie",
    "@pelisdeestrenos2026", "@Sub_esp_moviesXD", "@Anime_Waves_Chat", "@Grupo_anim",
    "@alegrupodelcanal08", "@asia_50", "@afterenmilpedasoz", "@doramasymasGB", "@seriespeliculasasiaticas",
    "@DoramasAudioLatinoYSub", "@joseito_9722", "@pellloonnnTR"
]

async def main():
    await bot.start(bot_token=BOT_TOKEN)
    await user.start()
    await enviar(f"🚀 Indexador Render iniciado\n📊 {len(title_index)} títulos\n📋 {len(PENDIENTES)} canales")
    
    for c in PENDIENTES:
        if c not in canales:
            await enviar(f"🔍 {c}...")
            await indexar(c)
    
    await enviar(f"🎉 COMPLETO!\n📊 {len(title_index)} títulos\n📁 {len(canales)} canales")

# Servidor falso para Render
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
def s():
    p = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", p), H).serve_forever()
threading.Thread(target=s, daemon=True).start()

asyncio.run(main())

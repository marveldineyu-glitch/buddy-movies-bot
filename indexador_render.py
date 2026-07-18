import asyncio, pickle, json, os, re, time, hashlib, threading
from collections import defaultdict
from telethon import TelegramClient
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

# ⚙️ CONFIG
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
    with open(CANALES_FILE) as f:
        canales = json.load(f)

def guardar():
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump({'content_index': dict(content_index), 'title_index': title_index}, f)
    with open(CANALES_FILE, 'w') as f:
        json.dump(canales, f)

def limpiar(text):
    if not text: return "Sin título"
    text = re.sub(r'https?://\S+', '', text).replace('\n', ' ').strip()
    return text[:200] if len(text) > 10 else "Sin título"

class IndexerBot:
    def __init__(self):
        self.bot = None
        self.user = None
    
    async def initialize(self):
        self.user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
        await self.user.start()
        self.bot = TelegramClient('render_bot', API_ID, API_HASH)
        await self.bot.start(bot_token=BOT_TOKEN)
        print(f"✅ Indexador iniciado - {len(title_index)} títulos")
        await self.bot.send_message(ADMIN_ID, f"🚀 {len(title_index)} títulos | {len(canales)} canales")
    
    async def indexar(self, canal):
        try:
            ent = await self.user.get_entity(canal)
            count = 0
            async for m in self.user.iter_messages(ent, limit=2000):
                if m.media and m.text:
                    ct = limpiar(m.text)
                    words = re.findall(r'\b\w+\b', ct.lower())
                    md = {'canal': canal, 'titulo': ct, 'msg_id': m.id}
                    for k in set(w for w in words if len(w) > 2):
                        content_index[k].append(md)
                    title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
                    count += 1
            if canal not in canales:
                canales.append(canal)
            guardar()
            await self.bot.send_message(ADMIN_ID, f"✅ {canal}: {count}")
            return count
        except Exception as e:
            await self.bot.send_message(ADMIN_ID, f"❌ {canal}: {e}")
            return 0

PENDIENTES = [
    "@CineMaxService", "@PokemonDPSubEsp", "@pelis_series_anime_1209", "@kdramasflanes",
    "@doramasestrenos", "@DoramasGratiskDramaLovers", "@uno_mas_2033", "@Korean_doramas_top",
    "@doramasesptg", "@animesdetodoslosgeneros", "@peliculasdebarbie1", "@barbiepeliculass",
    "@barbieepeliculaspqsiixx", "@peliskun", "@pelisanimeymas", "@GRUPPETE_DE_PELICULA_ANIME_Y_MAS",
    "@the_Legend_Of_Tomiris_Movie", "@chicanosforever", "@pelisjokerHDelpapa", "@lanoviadeltitan",
    "@escatologiafilmesmovie", "@pelisdeestrenos2026", "@Sub_esp_moviesXD", "@Anime_Waves_Chat",
    "@Grupo_anim", "@alegrupodelcanal08", "@asia_50", "@afterenmilpedasoz", "@doramasymasGB",
    "@seriespeliculasasiaticas", "@DoramasAudioLatinoYSub", "@joseito_9722", "@pellloonnnTR"
]

async def main():
    bot = IndexerBot()
    await bot.initialize()
    for c in PENDIENTES:
        if c not in canales:
            await bot.bot.send_message(ADMIN_ID, f"🔍 {c}...")
            await bot.indexar(c)
    await bot.bot.send_message(ADMIN_ID, f"🎉 COMPLETO! {len(title_index)} títulos")
    await bot.bot.run_until_disconnected()

# Servidor falso
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
def s():
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()
threading.Thread(target=s, daemon=True).start()

print("✅ Servidor HTTP iniciado")
asyncio.run(main())

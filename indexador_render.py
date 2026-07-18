import asyncio, pickle, json, os, re, hashlib, time
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8463069047:AAGeZg0IQd-1-Mv3ubxqnwZY1oJgxio9hr8"
SESSION = "1AZWarzgBu7T0qCqBvsZnNQmCPiU-8vdteMOcKuPBC14WtUC7pT3QuAG55Y6GtlbkZZ8XN_KDugD214Jqe-XExmoCW-FJdoO-c0PIDpEnLXYM61XRIpMh-WolwbhREweQY0FeGVuR2PfpnSEMOqlwb3wUC3lRxS6zGV-QzwxmiB_cpXVpDoSn61poZTcevExy_ao5cKVV5Zzjc9QF7uEhaRhCiDbENWUoZOQGqMDG5iT9PdbUf_Hd9tYElcb4jXjegsTDH-baufMF00Rxqp2_GQvGLk7Tq8DZqnugeB0hzZHrLNTqPrH5V0lJURcJS-yswbganim5kTTG5auZG9TnllbT6iM5Mv8="
ADMIN_ID = 7771137226
ARCHIVO_INDEX = "video_index_masivo.pkl"
ARCHIVO_CANALES = "canales_indexados.json"

content_index = defaultdict(list)
title_index = {}
canales = []

if os.path.exists(ARCHIVO_INDEX):
    with open(ARCHIVO_INDEX, 'rb') as f:
        data = pickle.load(f)
        content_index = defaultdict(list, data.get('content_index', {}))
        title_index = data.get('title_index', {})
        print(f"📂 Cargados {len(title_index)} títulos")

if os.path.exists(ARCHIVO_CANALES):
    with open(ARCHIVO_CANALES) as f:
        canales = json.load(f)

def guardar_index():
    with open(ARCHIVO_INDEX, 'wb') as f:
        pickle.dump({'content_index': dict(content_index), 'title_index': title_index, 'timestamp': time.time()}, f)

def guardar_canales():
    with open(ARCHIVO_CANALES, 'w') as f:
        json.dump(canales, f)

async def enviar_progreso(msg):
    print(f'ENVIANDO: {msg}')
    await bot.send_message(ADMIN_ID, msg)
    print('ENVIADO')

def limpiar_titulo(text):
    if not text: return "Sin título"
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        if 5 <= len(line.split()) <= 20 and len(line) > 10:
            return line[:200]
    return lines[0][:200] if lines else "Sin título"

async def indexar_canal(canal):
    try:
        ent = await user.get_entity(canal)
        count = 0
        async for m in user.iter_messages(ent, limit=None):
            if m.media:
                es_video = False
                if hasattr(m.media, 'photo'):
                    continue
                elif hasattr(m.media, 'video'):
                    es_video = True
                elif hasattr(m.media, 'document'):
                    doc = m.media.document
                    if doc.mime_type and doc.mime_type.startswith('video/'):
                        es_video = True
                
                if es_video:
                    txt = m.text if m.text else ''
                    if txt and len(txt) >= 10:
                        ct = limpiar_titulo(txt)
                        words = re.findall(r'\b[a-zA-Z0-9áéíóúñ]+\b', ct.lower())
                        stop = {'de','la','el','y','en','con','para','por','un','una','hd','full','4k','1080p','720p','latino','español','subtitulado','the','and','with','for'}
                        kw = [w for w in words if w not in stop and len(w) > 2]
                        md = {'canal': canal, 'titulo': ct, 'msg_id': m.id}
                        for k in set(kw):
                            content_index[k].append(md)
                        title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
                        count += 1
                        if count % 500 == 0:
                            await enviar_progreso(f"📊 {canal}: {count} títulos...")
                            guardar_index()
        
        if canal not in canales:
            canales.append(canal)
            guardar_canales()
        
        guardar_index()
        await enviar_progreso(f"✅ {canal}: {count} títulos")
        return count
    except Exception as e:
        await enviar_progreso(f"❌ {canal}: {e}")
        return 0

bot = TelegramClient('index_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

CANALES_PENDIENTES = [
    "@SeriesAnimadasbyJoel", "@peliculas2008", "@Estrenos1980s", "@seriesfurry", "@prdejooooo",
    "@Marvel_peliculas346", "@CineMaxService", "@PokemonDPSubEsp", "@pelis_series_anime_1209",
    "@kdramasflanes", "@doramasestrenos", "@DoramasGratiskDramaLovers", "@uno_mas_2033",
    "@Korean_doramas_top", "@doramasesptg", "@animesdetodoslosgeneros", "@peliculasdebarbie1",
    "@barbiepeliculass", "@barbieepeliculaspqsiixx", "@peliskun", "@pelisanimeymas",
    "@GRUPPETE_DE_PELICULA_ANIME_Y_MAS", "@the_Legend_Of_Tomiris_Movie", "@chicanosforever",
    "@pelisjokerHDelpapa", "@lanoviadeltitan", "@escatologiafilmesmovie", "@pelisdeestrenos2026",
    "@Sub_esp_moviesXD", "@Anime_Waves_Chat", "@Grupo_anim", "@alegrupodelcanal08", "@asia_50",
    "@afterenmilpedasoz", "@doramasymasGB", "@seriespeliculasasiaticas", "@DoramasAudioLatinoYSub",
    "@Solo_Leveling_TEMPORADA", "@joseito_9722"
]

@bot.on(events.NewMessage(pattern='/add'))
async def add_canal(event):
    if event.sender_id != ADMIN_ID: return
    texto = event.text.replace('/add', '').strip()
    nuevos = re.findall(r'@\w+', texto)
    if not nuevos:
        await event.reply("❌ /add @canal1 @canal2")
        return
    for c in nuevos:
        if c not in CANALES_PENDIENTES and c not in canales:
            CANALES_PENDIENTES.append(c)
            await event.reply(f"✅ {c} añadido a la cola")
        else:
            await event.reply(f"⏭️ {c} ya está")

@bot.on(events.NewMessage(pattern='/progreso'))
async def progreso(event):
    if event.sender_id != ADMIN_ID: return
    await event.reply(f"📊 {len(title_index)} títulos | 📁 {len(canales)} canales | 📋 {len(CANALES_PENDIENTES)} pendientes")

async def main():
    await user.start()
    await enviar_progreso(f"🚀 Indexador iniciado\n📊 {len(title_index)} títulos cargados\n📋 {len(CANALES_PENDIENTES)} canales por indexar")
    
    for canal in CANALES_PENDIENTES:
        if canal in canales:
            await enviar_progreso(f"⏭️ {canal} ya indexado")
            continue
        await enviar_progreso(f"🔍 Iniciando {canal}...")
        await indexar_canal(canal)
        await asyncio.sleep(2)
    
    await enviar_progreso(f"🎉 INDEXACIÓN COMPLETA!\n📊 Total: {len(title_index)} títulos\n📁 {len(canales)} canales")
    guardar_index()
    guardar_canales()

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

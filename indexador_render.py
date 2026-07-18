import asyncio, pickle, json, os, re, hashlib, time
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
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
                # Solo videos
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
                    txt = m.text or m.caption or ''
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
                        if count % 200 == 0:
                            print(f"   {canal}: {count} títulos...")
                            guardar_index()
        
        if canal not in canales:
            canales.append(canal)
            guardar_canales()
        
        guardar_index()
        print(f"✅ {canal}: {count} títulos")
        return count
    except Exception as e:
        print(f"❌ {canal}: {e}")
        return 0

bot = TelegramClient('index_render_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Lista de canales a indexar
CANALES_PENDIENTES = [
    "@animescompletosespanol", "@Animetimeee", "@peliculajuventud", "@detectiveconanES", "@peliculasCalderon",
    "@yugiohesp", "@inuyashaJH", "@pellloonnnTR", "@EmmaAnimesWorld26", "@silavidatedamandarina",
    "@maisseriesenovelas", "@seriesblsubesp", "@Tododragonballenlatino", "@terecomiendopelis2026", "@peliculasghiblive",
    "@mundocinelat", "@CineOchentero", "@Cinesombras", "@peliparatodos01", "@pidetupeliculaaca",
    "@pelisfamilia", "@pelisdocumentales", "@Loquemastegusta007", "@animes_amv2021", "@KaijuNo8EnLatino",
    "@AnimeZeus3", "@SeriesAnimadasbyJoel", "@peliculas2008", "@Estrenos1980s", "@seriesfurry",
    "@prdejooooo", "@Marvel_peliculas346", "@CineMaxService", "@PokemonDPSubEsp", "@pelis_series_anime_1209",
    "@kdramasflanes", "@doramasestrenos", "@DoramasGratiskDramaLovers", "@uno_mas_2033", "@Korean_doramas_top",
    "@doramasesptg", "@animesdetodoslosgeneros", "@peliculasdebarbie1", "@barbiepeliculass", "@barbieepeliculaspqsiixx",
    "@peliskun", "@pelisanimeymas", "@GRUPPETE_DE_PELICULA_ANIME_Y_MAS", "@the_Legend_Of_Tomiris_Movie",
    "@chicanosforever", "@pelisjokerHDelpapa", "@lanoviadeltitan", "@escatologiafilmesmovie", "@pelisdeestrenos2026",
    "@Sub_esp_moviesXD", "@Anime_Waves_Chat", "@Grupo_anim", "@alegrupodelcanal08", "@asia_50",
    "@afterenmilpedasoz", "@doramasymasGB", "@seriespeliculasasiaticas", "@DoramasAudioLatinoYSub", "@Solo_Leveling_TEMPORADA"
]

async def main():
    await user.start()
    print(f"✅ Indexador Render iniciado")
    print(f"📊 {len(title_index)} títulos | {len(canales)} canales")
    print(f"📋 {len(CANALES_PENDIENTES)} canales por indexar")
    
    for canal in CANALES_PENDIENTES:
        if canal in canales:
            print(f"⏭️ {canal} ya indexado, saltando...")
            continue
        print(f"\n🔍 Indexando {canal}...")
        await indexar_canal(canal)
        await asyncio.sleep(2)
    
    print(f"\n🎉 INDEXACIÓN COMPLETA!")
    print(f"📊 Total: {len(title_index)} títulos")
    print(f"📁 {len(canales)} canales")
    guardar_index()
    guardar_canales()

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

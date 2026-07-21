import asyncio, pickle, json, os, re, time
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "7812301734:AAHIXx70G83tb41pBczdCcdhHRiBlz43g7A"
SESSION = "1AZWarzoBuxvdHSrwtgONsPYL0vKf3uziv8FPQQhCCyYEV34mk1U3qTBgYdEVU9h9FOSgNCm1hBJs23Exo0LSdX0BpCIYTuyMDYD08AitO-3HzlFZaiEs4EGlXTXfE7CRV_ZlsZ3rxWSTs6jW2_DRQYZl174Tne2BgJQTusuYE8ipcm6H0EuJgwqFmVZ40kOD_S3XpMrin9EIQqqkgbUMLJ6TXZ2cUikMcHBDIoZ7UrlKvLt__vE-GKTSgzSU61PtG8-lLiysQ2EwQ3tU6tBwDqoa1NlEzw142Yc_80PqqvzFqWSTWrK3JcYGSI2hsPxrv8d2ig2eWsH9FgGM8k6rv93y2WHx0s8="
ARCHIVO = "video_index_rapido.pkl"
CANALES_FILE = "canales_rapido.json"

title_index = {}
canales = []

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, 'rb') as f:
        title_index = pickle.load(f).get('title_index', {})

if os.path.exists(CANALES_FILE):
    with open(CANALES_FILE) as f:
        canales = json.load(f)

def guardar():
    with open(ARCHIVO, 'wb') as f:
        pickle.dump({'title_index': title_index}, f)
    with open(CANALES_FILE, 'w') as f:
        json.dump(canales, f)

async def indexar(canal):
    try:
        ent = await user.get_entity(canal)
        count = 0
        async for m in user.iter_messages(ent, limit=None):
            if m.media and hasattr(m.media, 'document'):
                doc = m.media.document
                if doc.mime_type and doc.mime_type.startswith('video/'):
                    txt = m.text or ''
                    if txt and len(txt) >= 5:
                        # Solo guardar título + enlace
                        c = canal.replace('@', '')
                        title_index[str(m.id)] = {
                            'titulo': txt.split('\n')[0][:200],
                            'canal': c,
                            'msg_id': m.id,
                            'enlace': f'https://t.me/{c}/{m.id}'
                        }
                        count += 1
        if canal not in canales:
            canales.append(canal)
        guardar()
        print(f"✅ {canal}: {count}")
        return count
    except Exception as e:
        print(f"❌ {canal}: {e}")
        return 0

bot = TelegramClient('rapido_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
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
    await user.start()
    for c in PENDIENTES:
        if c not in canales:
            await indexar(c)
    print(f"\n🎉 Completo: {len(title_index)} títulos")

asyncio.run(main())

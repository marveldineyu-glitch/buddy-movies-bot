import asyncio, re, json, os, pickle, hashlib, time
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ============================================
# ⚙️ CONFIGURACIÓN
# ============================================
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "7812301734:AAHIXx70G83tb41pBczdCcdhHRiBlz43g7A"
SESSION = "1AZWarzoBuxvdHSrwtgONsPYL0vKf3uziv8FPQQhCCyYEV34mk1U3qTBgYdEVU9h9FOSgNCm1hBJs23Exo0LSdX0BpCIYTuyMDYD08AitO-3HzlFZaiEs4EGlXTXfE7CRV_ZlsZ3rxWSTs6jW2_DRQYZl174Tne2BgJQTusuYE8ipcm6H0EuJgwqFmVZ40kOD_S3XpMrin9EIQqqkgbUMLJ6TXZ2cUikMcHBDIoZ7UrlKvLt__vE-GKTSgzSU61PtG8-lLiysQ2EwQ3tU6tBwDqoa1NlEzw142Yc_80PqqvzFqWSTWrK3JcYGSI2hsPxrv8d2ig2eWsH9FgGM8k6rv93y2WHx0s8="
ADMIN_ID = 7771137226
ARCHIVO_INDEX = "video_index_masivo.pkl"
ARCHIVO_CANALES = "canales_indexados.json"

bot = TelegramClient('indexador_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Índice masivo
content_index = defaultdict(list)
title_index = {}
canales = []

# Cargar existente
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
    data = {
        'content_index': dict(content_index),
        'title_index': title_index,
        'timestamp': time.time()
    }
    with open(ARCHIVO_INDEX, 'wb') as f:
        pickle.dump(data, f)

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

async def indexar_mensaje(m, canal):
    try:
        txt = m.text or m.caption or ''
        if not txt or len(txt) < 10: return  # Ignorar mensajes sin texto o muy cortos
        
        ct = limpiar_titulo(txt)
        words = re.findall(r'\b[a-zA-Z0-9áéíóúñ]+\b', ct.lower())
        stop = {'de','la','el','y','en','con','para','por','un','una','hd','full','4k','1080p','720p','latino','español','subtitulado','the','and','with','for'}
        kw = [w for w in words if w not in stop and len(w) > 2]
        
        md = {
            'canal': canal,
            'titulo': ct,
            'msg_id': m.id,
            'tamano': getattr(m.media, 'document', None) and getattr(m.media.document, 'size', 0) or 0
        }
        
        for k in set(kw):
            content_index[k].append(md)
        
        title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
        return True
    except:
        return False

async def indexar_canal(canal, event=None):
    try:
        ent = await user.get_entity(canal)
        count = 0
        async for m in user.iter_messages(ent, limit=None):
            # Solo indexar VIDEOS (ignorar fotos, stickers, etc)
            es_video = False
            if m.media:
                # SOLO videos reales, IGNORAR fotos
                es_video = False
                # Ignorar explícitamente fotos
                if hasattr(m.media, 'photo'):
                    es_video = False
                elif hasattr(m.media, 'video'):
                    es_video = True
                elif hasattr(m.media, 'document'):
                    doc = m.media.document
                    if doc.mime_type and doc.mime_type.startswith('video/'):
                        es_video = True
            if es_video:
                if await indexar_mensaje(m, canal):
                    count += 1
                    if count % 100 == 0:
                        print(f"   {canal}: {count} títulos...")
                        guardar_index()
        
        if canal not in canales:
            canales.append(canal)
            guardar_canales()
        
        print(f"✅ {canal}: {count} títulos")
        if event:
            await event.reply(f"✅ {canal}: {count} títulos")
        return count
    except Exception as e:
        print(f"❌ {canal}: {e}")
        if event:
            await event.reply(f"❌ {canal}: {e}")
        return 0

@bot.on(events.NewMessage(pattern='/addchannel'))
async def addchannel(event):
    if event.sender_id != ADMIN_ID: return
    
    texto = event.text.replace('/addchannel', '').strip()
    nuevos = re.findall(r'@\w+', texto)
    
    if not nuevos:
        await event.reply("❌ Formato: /addchannel @canal1 @canal2")
        return
    
    msg = await event.reply(f"⏳ Indexando {len(nuevos)} canales...")
    
    total = 0
    for i, canal in enumerate(nuevos):
        if canal in canales:
            await event.reply(f"⚠️ {canal} ya fue indexado")
            continue
        
        c = await indexar_canal(canal)
        total += c
        await asyncio.sleep(1)
    
    guardar_index()
    guardar_canales()
    await msg.edit(f"✅ **{total}** títulos nuevos.\n📊 Total general: **{len(title_index)}** títulos.\n📁 {len(canales)} canales indexados.")

@bot.on(events.NewMessage(pattern='/total'))
async def total(event):
    await event.reply(f"📊 **{len(title_index)}** títulos\n📁 **{len(canales)}** canales\n💾 Archivo: {ARCHIVO_INDEX}")

@bot.on(events.NewMessage(pattern='/canales'))
async def listar_canales(event):
    await event.reply("📁 **Canales indexados:**\n" + "\n".join(canales[:50]) + (f"\n...y {len(canales)-50} más" if len(canales) > 50 else ""))

@bot.on(events.NewMessage(pattern='/exportar'))
async def exportar(event):
    if event.sender_id != ADMIN_ID: return
    
    # Crear JSON ligero para D1
    export = []
    for k, v in title_index.items():
        export.append({
            "t": v['titulo'][:200],
            "c": v['canal'],
            "m": v['msg_id']
        })
    
    with open('export_d1.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False)
    
    await event.reply(f"✅ Exportados {len(export)} títulos a export_d1.json")

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Indexador masivo listo")
    print(f"📊 {len(title_index)} títulos | {len(canales)} canales")
    print(f"\nComandos:")
    print(f"  /addchannel @canal1 @canal2 - Indexar canales")
    print(f"  /total - Ver estadísticas")
    print(f"  /canales - Listar canales")
    print(f"  /exportar - Exportar para D1")
    await bot.run_until_disconnected()

asyncio.run(main())

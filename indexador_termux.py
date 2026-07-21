import asyncio, pickle, json, os, re, hashlib, time
from collections import defaultdict
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
SESSION = "1AZWarzoBuxvdHSrwtgONsPYL0vKf3uziv8FPQQhCCyYEV34mk1U3qTBgYdEVU9h9FOSgNCm1hBJs23Exo0LSdX0BpCIYTuyMDYD08AitO-3HzlFZaiEs4EGlXTXfE7CRV_ZlsZ3rxWSTs6jW2_DRQYZl174Tne2BgJQTusuYE8ipcm6H0EuJgwqFmVZ40kOD_S3XpMrin9EIQqqkgbUMLJ6TXZ2cUikMcHBDIoZ7UrlKvLt__vE-GKTSgzSU61PtG8-lLiysQ2EwQ3tU6tBwDqoa1NlEzw142Yc_80PqqvzFqWSTWrK3JcYGSI2hsPxrv8d2ig2eWsH9FgGM8k6rv93y2WHx0s8="
INDEX_FILE = "video_index_final.pkl"
CANALES_FILE = "canales_final.json"

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
    print(f"\n🔍 {canal}...")
    try:
        ent = await user.get_entity(canal)
        count = 0; t = time.time()
        async for m in user.iter_messages(ent, limit=None):
            if m.media and m.text:
                ct = limpiar(m.text)
                words = re.findall(r'\b\w+\b', ct.lower())
                md = {'canal': canal, 'titulo': ct, 'msg_id': m.id}
                for k in set(w for w in words if len(w) > 2):
                    content_index[k].append(md)
                title_index[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
                count += 1
                if count % 2000 == 0:
                    guardar()
                    print(f"   {canal}: {count} ({time.time()-t:.0f}s)")
        if canal not in canales: canales.append(canal)
        guardar()
        print(f"✅ {canal}: {count} ({time.time()-t:.0f}s) | Total: {len(title_index)}")
    except Exception as e:
        print(f"❌ {canal}: {e}")

async def main():
    global user
    user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await user.start()
    print(f"🚀 Indexador | {len(title_index)} títulos | {len(canales)} canales")
    print("Escribe @canal para indexar\n")
    while True:
        c = input("> ").strip()
        if c.lower() == 'salir': break
        if c.startswith('@'):
            if c not in canales:
                await indexar(c)
            else:
                print(f"⏭️ {c} ya indexado")
        elif c:
            # Aceptar lista de canales separados por espacio
            for canal in c.split():
                if canal.startswith('@') and canal not in canales:
                    await indexar(canal)

asyncio.run(main())

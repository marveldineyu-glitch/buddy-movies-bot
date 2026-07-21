import asyncio, re, json, os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

# ============================================
# ⚙️ CONFIGURACIÓN
# ============================================
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8845956181:AAGRxHDEC9DVwNmDT-4ae3KOvDHA46ISRTY"
SESSION = "1AZWarzoBuxvdHSrwtgONsPYL0vKf3uziv8FPQQhCCyYEV34mk1U3qTBgYdEVU9h9FOSgNCm1hBJs23Exo0LSdX0BpCIYTuyMDYD08AitO-3HzlFZaiEs4EGlXTXfE7CRV_ZlsZ3rxWSTs6jW2_DRQYZl174Tne2BgJQTusuYE8ipcm6H0EuJgwqFmVZ40kOD_S3XpMrin9EIQqqkgbUMLJ6TXZ2cUikMcHBDIoZ7UrlKvLt__vE-GKTSgzSU61PtG8-lLiysQ2EwQ3tU6tBwDqoa1NlEzw142Yc_80PqqvzFqWSTWrK3JcYGSI2hsPxrv8d2ig2eWsH9FgGM8k6rv93y2WHx0s8="
SEARCH_BOT1 = "@AutoFilter_Robot"
SEARCH_BOT3 = "@TlgramMovieSearch_Bot"
SEARCH_GROUP2 = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
ARCHIVO_DB = "titulos_enlaces.json"

bot = TelegramClient('indexador_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Base de datos local
db = {}
if os.path.exists(ARCHIVO_DB):
    with open(ARCHIVO_DB, 'r') as f:
        db = json.load(f)

def guardar_db():
    with open(ARCHIVO_DB, 'w') as f:
        json.dump(db, f, ensure_ascii=False)

def extraer_enlace(msg, chat_id, username):
    """Extrae el enlace de un mensaje"""
    if hasattr(msg, 'media') and msg.media:
        # Es un archivo, el enlace se genera cuando se sube al canal
        return None
    # Intentar extraer enlace del texto
    match = re.search(r'https://t\.me/[^\s]+', msg.text or '')
    return match.group(0) if match else None

def extraer_titulo(text):
    """Limpia y extrae el título"""
    if not text: return None
    # Quitar emojis y caracteres especiales
    text = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ\-\.]', '', text)
    text = text.strip()
    if len(text) < 5: return None
    return text[:200]

@user.on(events.NewMessage(chats=[SEARCH_BOT1, SEARCH_BOT3]))
async def capturar_bot1(event):
    """Captura resultados de bots de chat privado"""
    m = event.message
    if not m.text: return
    
    # Ignorar mensajes basura
    if any(x in m.text.lower() for x in ["save the file", "will be deleted", "select language", "no results", "not available"]):
        return
    
    # Extraer resultados de la lista
    if "Search Query" in m.text or "Results Found" in m.text or "Resultados para" in m.text:
        # Extraer título de búsqueda
        query = re.search(r'`([^`]+)`', m.text)
        query = query.group(1) if query else None
        
        # Extraer títulos individuales de los resultados
        titulos = re.findall(r'🎬\s*\d+\.?\s*(.+?)(?:\s*—|$)', m.text)
        if not titulos:
            titulos = re.findall(r'\d+\.?\s*\*\*(.+?)\*\*', m.text)
        
        for t in titulos:
            t = extraer_titulo(t)
            if t and t not in db:
                db[t] = {"query": query, "fuente": "bot1"}
                print(f"📝 {t[:80]}")
        
        guardar_db()

@user.on(events.NewMessage(chats=[SEARCH_GROUP2]))
async def capturar_bot2(event):
    """Captura resultados del bot de grupo"""
    m = event.message
    if not m.sender or not m.sender.bot: return
    if not m.text: return
    
    if any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]):
        return
    
    if m.media:
        # Guardar el archivo en el canal y obtener enlace
        raw = m.text or ""
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        
        # Extraer título del caption
        titulo = extraer_titulo(raw.split('\n')[0])
        if titulo and titulo not in db:
            db[titulo] = {"enlace": link, "fuente": "bot2"}
            print(f"🔗 {titulo[:80]} -> {link}")
        
        guardar_db()

@user.on(events.MessageEdited(chats=[SEARCH_GROUP2]))
async def capturar_bot2_edit(event):
    """Captura resultados editados del bot de grupo"""
    m = event.message
    if not m.sender or not m.sender.bot: return
    if not m.text: return
    
    if any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]):
        return
    
    # Extraer resultados
    titulos = re.findall(r'\d+\.\s*\*\*(.+?)\*\*', m.text)
    if not titulos:
        titulos = re.findall(r'\d+\.?\s*(.+?)(?:\s*—|$)', m.text)
    
    query = re.search(r'"(.*?)"', m.text)
    query = query.group(1) if query else None
    
    for t in titulos:
        t = extraer_titulo(t)
        if t and t not in db:
            db[t] = {"query": query, "fuente": "bot2_edit"}
            print(f"📝 {t[:80]}")
    
    guardar_db()

# ============================================
# COMANDOS
# ============================================
@bot.on(events.NewMessage(pattern='/total'))
async def total(event):
    await event.reply(f"📊 **{len(db)}** títulos indexados en la base de datos.")

@bot.on(events.NewMessage(pattern='/buscartodo'))
async def buscar_todo(event):
    """Busca masivamente para llenar la base de datos"""
    if event.sender_id != 7771137226: return
    
    # Lista de búsquedas populares
    busquedas = [
        "Naruto", "Pokemon", "Dragon Ball", "One Piece", "Avengers",
        "Batman", "Superman", "Spider Man", "Iron Man", "Thor",
        "Star Wars", "Harry Potter", "El Señor de los Anillos", "Matrix",
        "Avatar", "Titanic", "Jurassic Park", "Terminator", "Robocop",
        "Shrek", "Toy Story", "Frozen", "Coco", "Encanto",
        "anime", "pelicula", "series", "estreno", "2024",
        "acción", "comedia", "terror", "romance", "aventura",
        "latino", "español", "sub", "1080p", "4K"
    ]
    
    count = 0
    for q in busquedas:
        await user.send_message(SEARCH_BOT1, q)
        await user.send_message(SEARCH_GROUP2, f"/search {q}")
        await user.send_message(SEARCH_BOT3, q)
        count += 1
        if count % 3 == 0:
            await asyncio.sleep(5)  # Pausa cada 3 búsquedas
    
    await event.reply(f"✅ {len(busquedas)} búsquedas enviadas a 3 motores.")

@bot.on(events.NewMessage(pattern='/exportar'))
async def exportar(event):
    if event.sender_id != 7771137226: return
    await event.reply(f"📊 {len(db)} títulos en la base.\nArchivo: {ARCHIVO_DB}")

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print(f"✅ Indexador masivo activo - {len(db)} títulos en DB")
    print(f"📁 Archivo: {ARCHIVO_DB}")
    print(f"\nComandos:")
    print(f"  /total - Ver cantidad de títulos")
    print(f"  /buscartodo - Llenar DB con búsquedas")
    print(f"  /exportar - Ver estado")
    print(f"\nEscribe nombres de películas en @BuddyMovies_official para indexar")
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

asyncio.run(main())

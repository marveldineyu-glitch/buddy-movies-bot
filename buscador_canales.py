import asyncio, json, time
from telethon import TelegramClient, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.functions.contacts import SearchRequest

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
SESSION = "1AZWarzoBuxvdHSrwtgONsPYL0vKf3uziv8FPQQhCCyYEV34mk1U3qTBgYdEVU9h9FOSgNCm1hBJs23Exo0LSdX0BpCIYTuyMDYD08AitO-3HzlFZaiEs4EGlXTXfE7CRV_ZlsZ3rxWSTs6jW2_DRQYZl174Tne2BgJQTusuYE8ipcm6H0EuJgwqFmVZ40kOD_S3XpMrin9EIQqqkgbUMLJ6TXZ2cUikMcHBDIoZ7UrlKvLt__vE-GKTSgzSU61PtG8-lLiysQ2EwQ3tU6tBwDqoa1NlEzw142Yc_80PqqvzFqWSTWrK3JcYGSI2hsPxrv8d2ig2eWsH9FgGM8k6rv93y2WHx0s8="

# Palabras clave para buscar canales
QUERIES = [
    "peliculas", "cine", "series", "anime", "estrenos", "latino",
    "español", "castellano", "hd", "completas", "mega", "descargar",
    "ver online", "gratis", "cartelera", "film", "movies", "pelis",
    "subtitulado", "doblado", "1080p", "720p", "4k", "bluray",
    "netflix", "disney", "marvel", "dc", "terror", "comedia",
    "accion", "drama", "animacion", "documental", "indie"
]

# Cargar canales ya conocidos
try:
    with open("canales_video.json") as f:
        canales_conocidos = set(json.load(f))
except:
    canales_conocidos = set()

canales_encontrados = set()

def es_espanol(texto):
    """Verifica si el texto contiene palabras en español"""
    palabras_espanol = ['español', 'latino', 'castellano', 'mexico', 'argentina', 
                        'españa', 'doblado', 'subtitulado', 'sub', 'lat', 'esp']
    texto_lower = texto.lower()
    return any(p in texto_lower for p in palabras_espanol)

async def verificar_canal(client, canal_entity):
    """Verifica cuántos videos tiene un canal y si está en español"""
    try:
        # Contar videos
        count = 0
        textos_muestra = []
        
        async for m in client.iter_messages(
            canal_entity, 
            limit=100, 
            filter=types.InputMessagesFilterVideo
        ):
            if m.text:
                textos_muestra.append(m.text.lower())
                count += 1
            if count >= 100:
                break
        
        # Verificar si es español
        es_esp = any(es_espanol(t) for t in textos_muestra) if textos_muestra else False
        
        # Si tiene videos pero la muestra es pequeña, contar total
        if count >= 100 and es_esp:
            total = 0
            async for _ in client.iter_messages(
                canal_entity, 
                limit=500, 
                filter=types.InputMessagesFilterVideo
            ):
                total += 1
            return total, True
        
        return count, es_esp
        
    except Exception as e:
        return 0, False

async def buscar_canales():
    print(f"🔍 BUSCANDO CANALES CON +500 VIDEOS EN ESPAÑOL\n")
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    
    todos_resultados = []
    
    for query in QUERIES:
        print(f"🔎 Buscando: '{query}'...", end=" ", flush=True)
        try:
            # Buscar canales/grupos
            result = await client(SearchRequest(
                q=query,
                limit=20
            ))
            
            canales_query = 0
            for chat in result.chats:
                if hasattr(chat, 'username') and chat.username:
                    nombre = f"@{chat.username}"
                    if nombre not in canales_conocidos and nombre not in canales_encontrados:
                        canales_encontrados.add(nombre)
                        canales_query += 1
            
            print(f"{canales_query} canales")
            await asyncio.sleep(1)  # Pausa para no saturar
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            await asyncio.sleep(2)
    
    print(f"\n📊 Total canales únicos encontrados: {len(canales_encontrados)}")
    print(f"\n🔍 Verificando videos por canal...\n")
    
    canales_validos = []
    
    for i, canal in enumerate(list(canales_encontrados)):
        print(f"[{i+1}/{len(canales_encontrados)}] {canal}...", end=" ", flush=True)
        
        try:
            entity = await client.get_entity(canal)
            total, es_esp = await verificar_canal(client, entity)
            
            if total >= 500 and es_esp:
                print(f"✅ {total} videos (ESPAÑOL)")
                canales_validos.append({
                    'canal': canal,
                    'videos': total,
                    'titulo': entity.title
                })
            elif total >= 500:
                print(f"⚠️ {total} videos (no español)")
            else:
                print(f"❌ {total} videos")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
        
        await asyncio.sleep(1)  # Pausa entre verificaciones
    
    # Guardar resultados
    with open("canales_descubiertos.json", "w") as f:
        json.dump(canales_validos, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"🎉 CANALES VÁLIDOS (+500 videos, español):")
    for c in canales_validos:
        print(f"  ✅ {c['canal']} - {c['videos']} videos - {c['titulo'][:50]}")
    print(f"\n📊 Total: {len(canales_validos)} canales")
    print(f"💾 Guardado en canales_descubiertos.json")
    
    await client.disconnect()

asyncio.run(buscar_canales())

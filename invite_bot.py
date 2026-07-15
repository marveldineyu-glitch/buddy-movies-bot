import asyncio, json, os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8845956181:AAGRxHDEC9DVwNmDT-4ae3KOvDHA46ISRTY"
SESSION = "1AZWarzsBu3ri9Gnio07Z2btqD5PSNKdI84rIlVS7ESw_bUysWoiJgsuA6tIDh8sDWMaUapbBewnFLN-n21ZzyQlY33iehRVgAfvIb5eJXDEQMupddF6EAOm8hEaJL4A5Eeo1loOmTPZmqBLmLYhRk_er0u3tILqu5wZMwWzjUeq3A_6XEO_xqofyvMAvUpmXHYzdGXaBn-A0fi52LCP9oRd1JbhKGirKyW8BNhJJt0uL4ngJoH0W0-uPXMCY15n58N333yO1ILbWbDvtuQH7i3rRJP82yIindceDbNNK5gWtQFhTh73nT4Dxjqo0lcWwhOWpMOUJn1FvCQeViaZ1aKW49ay97io="
GRUPO_ID = -1002311102965
ADMIN_ID = 7771137226
META = 5
ENLACE = "https://t.me/BuddyMovies_official/1088"

bot = TelegramClient('invite_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
pendientes = {}
activo = False
solo_nuevos = False
archivo = "pendientes.json"
avisos = {}

if os.path.exists(archivo):
    with open(archivo) as f: pendientes = json.load(f)

def guardar():
    with open(archivo, 'w') as f: json.dump(pendientes, f)

@bot.on(events.ChatAction(chats=[GRUPO_ID]))
async def chat_action(event):
    try: await event.delete()
    except: pass
    
    if event.user_joined and solo_nuevos:
        uid = str(event.user.id)
        pendientes[uid] = 0
        guardar()
        name = event.user.first_name or "Usuario"
        msg = await bot.send_message(GRUPO_ID,
            f"🍿 Hola {name}, necesitás añadir a {META} amigos al grupo para poder escribir.\n\n"
            f"📊 Progreso: 0/{META}\n\n"
            f"👇 ¡Es muy fácil! Solo sigue estos pasos:",
            buttons=[[Button.url("👉 CLICK AQUÍ 👈", ENLACE)]])
        avisos[uid] = msg.id
    
    if event.user_added and event.action_message and event.action_message.from_id:
        uid = str(event.action_message.from_id.user_id)
        if uid in pendientes:
            pendientes[uid] += 1
            guardar()
            if pendientes[uid] >= META:
                del pendientes[uid]
                guardar()
                try:
                    ent = await bot.get_entity(int(uid))
                    await bot.edit_permissions(GRUPO_ID, int(uid), send_messages=True)
                    await bot.send_message(GRUPO_ID, f"✅ {ent.first_name}, ya puedes hablar en el grupo.")
                    if uid in avisos:
                        try: await bot.delete_messages(GRUPO_ID, avisos[uid])
                        except: pass
                        del avisos[uid]
                except: pass

@bot.on(events.NewMessage(chats=[GRUPO_ID]))
async def filtrar(event):
    if event.out or event.sender_id == ADMIN_ID: return
    if event.text and event.text.startswith('/'): return
    uid = str(event.sender_id)
    if not activo or uid not in pendientes: return
    
    await event.delete()
    await bot.edit_permissions(GRUPO_ID, event.sender_id, send_messages=False)
    
    count = pendientes[uid]
    barra = "🟩" * count + "⬜" * (META - count)
    name = (await event.get_sender()).first_name or "Usuario"
    
    msg = await bot.send_message(GRUPO_ID,
        f"🍿 Hola {name}, necesitás añadir a {META} amigos al grupo para poder escribir.\n\n"
        f"📊 Progreso: [{barra}] {count}/{META}\n\n"
        f"👇 ¡Es muy fácil! Solo sigue estos pasos:",
        buttons=[[Button.url("👉 CLICK AQUÍ 👈", ENLACE)]])
    avisos[uid] = msg.id

@bot.on(events.NewMessage(pattern='/reset'))
async def reset(event):
    if event.sender_id != ADMIN_ID: return
    global META, activo, solo_nuevos
    solo_nuevos = False
    try:
        p = event.text.split()
        if len(p) > 1: META = int(p[1])
    except: pass
    activo = True
    pendientes.clear()
    avisos.clear()
    async for m in bot.iter_participants(GRUPO_ID):
        if m.bot or m.id == ADMIN_ID: continue
        pendientes[str(m.id)] = 0
    guardar()
    await event.reply(f"✅ Modo restricción activado.\n👥 {len(pendientes)} miembros.\n📌 Deben añadir {META} personas para escribir.")

@bot.on(events.NewMessage(pattern='/lock'))
async def lock(event):
    if event.sender_id != ADMIN_ID: return
    global activo, solo_nuevos
    solo_nuevos = True
    activo = True
    pendientes.clear()
    avisos.clear()
    guardar()
    await event.reply(f"🔒 Solo nuevos miembros deberán añadir {META} personas.")

@bot.on(events.NewMessage(pattern='/free'))
async def free(event):
    if event.sender_id != ADMIN_ID: return
    global activo, solo_nuevos
    activo = False
    solo_nuevos = False
    pendientes.clear()
    avisos.clear()
    guardar()
    c = 0
    async for m in bot.iter_participants(GRUPO_ID):
        if m.bot or m.id == ADMIN_ID: continue
        try: await bot.edit_permissions(GRUPO_ID, m.id, send_messages=True); c += 1
        except: pass
    await event.reply(f"🔓 Sin restricciones. {c} miembros liberados.")

@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    modo = "Solo nuevos" if solo_nuevos else ("Activado" if activo else "Libre")
    await event.reply(f"⚙️ Panel | {modo} | Meta: {META} | Pendientes: {len(pendientes)}\n/reset <num> | /lock | /free")

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

print("✅ Bot de restricción activo")
asyncio.run(bot.run_until_disconnected())

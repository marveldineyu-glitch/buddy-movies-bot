import asyncio, json, os, re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8845956181:AAGRxHDEC9DVwNmDT-4ae3KOvDHA46ISRTY"
SESSION = "1AZWarzsBu3ri9Gnio07Z2btqD5PSNKdI84rIlVS7ESw_bUysWoiJgsuA6tIDh8sDWMaUapbBewnFLN-n21ZzyQlY33iehRVgAfvIb5eJXDEQMupddF6EAOm8hEaJL4A5Eeo1loOmTPZmqBLmLYhRk_er0u3tILqu5wZMwWzjUeq3A_6XEO_xqofyvMAvUpmXHYzdGXaBn-A0fi52LCP9oRd1JbhKGirKyW8BNhJJt0uL4ngJoH0W0-uPXMCY15n58N333yO1ILbWbDvtuQH7i3rRJP82yIindceDbNNK5gWtQFhTh73nT4Dxjqo0lcWwhOWpMOUJn1FvCQeViaZ1aKW49ay97io="
GRUPO_ID = 3327241039
ADMIN_ID = 7771137226
META_INVITADOS = 5

bot = TelegramClient('invite_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
invitaciones = {}
invitaciones_activas = False
archivo = "invitaciones.json"

if os.path.exists(archivo):
    with open(archivo) as f:
        invitaciones = json.load(f)

def guardar():
    with open(archivo, 'w') as f:
        json.dump(invitaciones, f)

@bot.on(events.ChatAction(chats=[GRUPO_ID]))
async def on_join(event):
    try: await event.delete()
    except: pass
    
    if event.user_joined:
        if not invitaciones_activas: return
        uid = str(event.user.id)
        name = event.user.first_name or "Usuario"
        invitaciones[uid] = 0
        guardar()
        try: await bot.edit_permissions(GRUPO_ID, event.user.id, send_messages=False)
        except: pass
        barra = "⬜" * META_INVITADOS
        await bot.send_message(GRUPO_ID, f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Estás RESTRINGIDO.\n🎯 Añade a {META_INVITADOS} amigos.\n📊 [{barra}] 0/{META_INVITADOS}")
    
    if event.user_added and event.action_message and event.action_message.from_id:
        inviter = str(event.action_message.from_id.user_id)
        if inviter in invitaciones:
            invitaciones[inviter] += 1
            guardar()
            if invitaciones[inviter] >= META_INVITADOS:
                del invitaciones[inviter]
                guardar()
                try:
                    ent = await bot.get_entity(int(inviter))
                    await bot.edit_permissions(GRUPO_ID, int(inviter), send_messages=True)
                    await bot.send_message(GRUPO_ID, f"🎉 **¡Felicidades {ent.first_name}!** Ya puedes escribir.")
                except: pass

@bot.on(events.NewMessage(chats=[GRUPO_ID]))
async def bloquear(event):
    if event.out: return
    uid = str(event.sender_id)
    if uid in invitaciones and invitaciones_activas:
        await event.delete()

@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    estado = "🔒 Activado" if invitaciones_activas else "🔓 Desactivado"
    await event.reply(f"⚙️ Panel\n{estado}\nMeta: {META_INVITADOS}\nPendientes: {len(invitaciones)}\n\n/reset <num>\n/free\n/lock")

@bot.on(events.NewMessage(pattern='/reset'))
async def reset(event):
    if event.sender_id != ADMIN_ID: return
    global META_INVITADOS, invitaciones_activas
    try:
        p = event.text.split()
        if len(p) > 1: META_INVITADOS = int(p[1])
    except: pass
    invitaciones_activas = True
    invitaciones.clear()
    async for m in bot.iter_participants(GRUPO_ID):
        if m.bot or m.id == ADMIN_ID: continue
        invitaciones[str(m.id)] = 0
        try: await bot.edit_permissions(GRUPO_ID, m.id, send_messages=False)
        except: pass
    guardar()
    await event.reply(f"✅ Meta: {META_INVITADOS}. {len(invitaciones)} restringidos.")

@bot.on(events.NewMessage(pattern='/free'))
async def free(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = False
    invitaciones.clear()
    guardar()
    c = 0
    async for m in bot.iter_participants(GRUPO_ID):
        if m.bot or m.id == ADMIN_ID: continue
        try: await bot.edit_permissions(GRUPO_ID, m.id, send_messages=True); c += 1
        except: pass
    await event.reply(f"🔓 {c} liberados.")

@bot.on(events.NewMessage(pattern='/lock'))
async def lock(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = True
    await event.reply("🔒 Activado.")

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

print("✅ Invite Bot listo")
asyncio.run(bot.run_until_disconnected())

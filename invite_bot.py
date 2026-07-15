import asyncio, json, os, re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8845956181:AAGRxHDEC9DVwNmDT-4ae3KOvDHA46ISRTY"
SESSION = "1AZWarzsBu3ri9Gnio07Z2btqD5PSNKdI84rIlVS7ESw_bUysWoiJgsuA6tIDh8sDWMaUapbBewnFLN-n21ZzyQlY33iehRVgAfvIb5eJXDEQMupddF6EAOm8hEaJL4A5Eeo1loOmTPZmqBLmLYhRk_er0u3tILqu5wZMwWzjUeq3A_6XEO_xqofyvMAvUpmXHYzdGXaBn-A0fi52LCP9oRd1JbhKGirKyW8BNhJJt0uL4ngJoH0W0-uPXMCY15n58N333yO1ILbWbDvtuQH7i3rRJP82yIindceDbNNK5gWtQFhTh73nT4Dxjqo0lcWwhOWpMOUJn1FvCQeViaZ1aKW49ay97io="
GRUPO_ID = 3327241039
ADMIN_ID = 7771137226
META_INVITADOS = 5
ENLACE = "https://t.me/BuddyMovies_official/1088"

bot = TelegramClient('invite_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
invitaciones = {}
invitaciones_activas = False
ya_escribieron = set()
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
        invitaciones[uid] = 0
        guardar()
    
    if event.user_added and event.action_message and event.action_message.from_id:
        inviter = str(event.action_message.from_id.user_id)
        if inviter in invitaciones:
            invitaciones[inviter] += 1
            guardar()
            count = invitaciones[inviter]
            if count >= META_INVITADOS:
                invitaciones.pop(inviter, None)
                ya_escribieron.discard(inviter)
                guardar()
                try:
                    ent = await bot.get_entity(int(inviter))
                    await bot.edit_permissions(GRUPO_ID, int(inviter), send_messages=True)
                    await bot.send_message(GRUPO_ID, f"🎉 **¡Felicidades {ent.first_name}!** Completaste la misión. ¡Ya puedes escribir!")
                except: pass

@bot.on(events.NewMessage(chats=[GRUPO_ID]))
async def bloquear(event):
    if event.out or event.sender_id == ADMIN_ID: return
    if event.text and event.text.startswith('/'): return
    
    uid = str(event.sender_id)
    
    if not invitaciones_activas: return
    print(f"DEBUG: uid={uid} en invitaciones={uid in invitaciones} en ya_escribieron={uid in ya_escribieron}")
    
    # Si es nuevo en modo activo, dejarlo escribir 1 vez
    if uid not in ya_escribieron:
        ya_escribieron.add(uid)
        if uid not in invitaciones:
            invitaciones[uid] = 0
            guardar()
        return
    
    # Ya escribió una vez, ahora restringir
    if uid in invitaciones:
        await event.delete()
        try:
            await bot.edit_permissions(GRUPO_ID, event.sender_id, send_messages=False)
        except: pass
        
        count = invitaciones[uid]
        barra = "🟩" * count + "⬜" * (META_INVITADOS - count)
        name = (await event.get_sender()).first_name or "Usuario"
        
        msg = f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Has sido RESTRINGIDO temporalmente.\nPara poder escribir aquí, debes completar la misión.\n\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos al grupo.\n\n📊 **TU PROGRESO ACTUAL:**\n[{barra}] {count}/{META_INVITADOS}\n\n👆 El contador se actualiza solo. ¡Invita y mira cómo sube!"
        
        await bot.send_message(GRUPO_ID, msg, buttons=[[Button.url("💡 ¿Cómo invitar?", ENLACE)]], link_preview=False)

@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    estado = "🔒 Activado" if invitaciones_activas else "🔓 Desactivado"
    await event.reply(f"⚙️ **Panel**\n{estado}\n📊 Meta: {META_INVITADOS}\n👤 Pendientes: {len(invitaciones)}\n\n🔄 /reset <num>\n🔓 /free\n🔒 /lock")

@bot.on(events.NewMessage(pattern='/reset'))
async def reset(event):
    if event.sender_id != ADMIN_ID: return
    global META_INVITADOS, invitaciones_activas, ya_escribieron
    try:
        p = event.text.split()
        if len(p) > 1: META_INVITADOS = int(p[1])
    except: pass
    invitaciones_activas = True
    invitaciones.clear()
    ya_escribieron.clear()
    guardar()
    await event.reply(f"✅ **Meta: {META_INVITADOS}.** Los usuarios podrán escribir 1 vez antes de ser restringidos.")

@bot.on(events.NewMessage(pattern='/free'))
async def free(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas, ya_escribieron
    invitaciones_activas = False
    invitaciones.clear()
    ya_escribieron.clear()
    guardar()
    c = 0
    async for m in bot.iter_participants(GRUPO_ID):
        if m.bot or m.id == ADMIN_ID: continue
        try: await bot.edit_permissions(GRUPO_ID, m.id, send_messages=True); c += 1
        except: pass
    await event.reply(f"🔓 **{c} usuarios liberados.**")

@bot.on(events.NewMessage(pattern='/lock'))
async def lock(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas, ya_escribieron
    invitaciones_activas = True
    ya_escribieron.clear()
    await event.reply("🔒 **Activado.** Nuevos podrán escribir 1 vez antes de ser restringidos.")

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

print("✅ Invite Bot - 1 mensaje libre")
asyncio.run(bot.run_until_disconnected())

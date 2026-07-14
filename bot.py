import asyncio, re, json, os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzoBuxWikHDKF_IbruT6fapmKISqelNWCOEwGENItsRxCcuHUSPuGq5tVPpUVoNuhJm3T6XNpX2oOQynZFnY1Mo8JIBOJ_hMxw9fZr71T2069YYGXueh1YkHKfpFJADfWNg9XJ6N2Gp_A_vvKZUkmEAcjmaVPmBg0CsEideHuzgYFbB2rkMmG7GwrB4bLTZy1_7jWP_xX4HanGT-GDS5Pi_ZbEyhQNZ54fA13ecKxO4Eu9ERK7ZGpIadk995GkcH7v2ibrj2pxxRb99uHpgjTxLy2EppT6Sd5Jic5HDS_MP_HsKVpKFY6iZo_jaAiNE4eRNEHJ6AUdSjnQpB6d9_DDT3I0c="
SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
GRUPO_ID = -1002311102965
ADMIN_ID = 7771137226
ENLACE_GRUPO = "https://t.me/BuddyMovies_official/1088"
META_INVITADOS = 5

# Anti-duplicado: solo una instancia
import socket
s = socket.socket()
try:
    s.bind(("0.0.0.0", 9999))
except:
    print("Otra instancia corriendo. Saliendo...")
    exit(0)

bot = TelegramClient('unified_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
active = {}
mirror = {}
sent_ids = set()  # Anti-eco
mirror_chat = {}

invitaciones = {}
invitaciones_activas = False
archivo_inv = "invitaciones.json"

if os.path.exists(archivo_inv):
    with open(archivo_inv) as f:
        invitaciones = json.load(f)

def guardar_inv():
    with open(archivo_inv, 'w') as f:
        json.dump(invitaciones, f)

SIN_RESULTADOS = "❌ **No se encontraron resultados.**"

def replace_ads(text):
    if not text: return text
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    return text

def make_buttons(msg):
    if not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = [Button.inline(btn.text, btn.data) if btn.data else Button.url(btn.text, btn.url) for btn in row]
        btns.append(r)
    return btns

def get_user():
    if not active: return None, None, "Usuario"
    valid = [k for k in active if k is not None]
    if not valid: return None, None, "Usuario"
    uid = valid[-1]
    return uid, active[uid]['chat'], active[uid]['name']

# ============ SISTEMA DE INVITACIONES ============
@bot.on(events.ChatAction(chats=[GRUPO_ID]))
async def on_join(event):
    try: await event.delete()
    except: pass
    
    if event.user_joined:
        name = event.user.first_name or "Usuario"
        welcome = f"🎬 **¡Bienvenido {name} a Buddy Movies!** 🍿\n\n📢 Busca películas y series escribiendo el nombre en el chat.\n\n🔥 Tenemos el mejor motor de búsqueda para encontrar el mejor contenido."
        await bot.send_message(GRUPO_ID, welcome)
        
        if not invitaciones_activas: return
        
        uid = str(event.user.id)
        invitaciones[uid] = 0
        guardar_inv()
        barra = "⬜" * META_INVITADOS
        msg = f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Estás RESTRINGIDO temporalmente.\nPara poder escribir aquí, debes completar la misión.\n\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos al grupo.\n\n💡Si no sabes cómo hacerlo Clic aquí 👇🏻\n{ENLACE_GRUPO}\n\n📊 **TU PROGRESO ACTUAL:**\nProgreso: [{barra}] 0/{META_INVITADOS}\n\n👆 El contador se actualiza solo. ¡Invita y mira cómo sube!"
        await bot.send_message(GRUPO_ID, msg)
    
    if event.user_added:
        if event.action_message and event.action_message.from_id:
            inviter_id = str(event.action_message.from_id.user_id)
            if inviter_id in invitaciones:
                invitaciones[inviter_id] += 1
                guardar_inv()
                count = invitaciones[inviter_id]
                if count >= META_INVITADOS:
                    del invitaciones[inviter_id]
                    guardar_inv()
                    try:
                        inviter = await bot.get_entity(int(inviter_id))
                        name = inviter.first_name or "Usuario"
                        await bot.edit_permissions(GRUPO_ID, int(inviter_id), send_messages=True)
                    except:
                        name = "Usuario"
                    await bot.send_message(GRUPO_ID, f"🎉 **¡Felicidades {name}!** Completaste la misión. ¡Ya puedes escribir!")

@bot.on(events.NewMessage(chats=[GRUPO_ID]))
async def anti_enlaces(event):
    if event.out: return
    
    if event.text and re.search(r'https?://|t\.me/', event.text) and event.sender_id != ADMIN_ID:
        await event.delete()
        return
    
    uid = str(event.sender_id)
    if uid in invitaciones and invitaciones_activas:
        await event.delete()
        count = invitaciones[uid]
        barra = "🟩" * count + "⬜" * (META_INVITADOS - count)
        try: await bot.send_message(GRUPO_ID, f"⛔ Completa la misión: [{barra}] {count}/{META_INVITADOS}")
        except: pass
        return
    # Si no está restringido y no es enlace, dejar pasar a on_user

# ============ COMANDOS ADMIN ============
@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    estado = "🔒 Activado" if invitaciones_activas else "🔓 Desactivado"
    await event.reply(f"⚙️ **PANEL DE ADMINISTRADOR**\n\n👥 **Estado:** {estado}\n📊 **Meta:** {META_INVITADOS} invitados\n👤 **Pendientes:** {len(invitaciones)} usuarios\n\n**Comandos:**\n🔄 /reset <num> - Activar y reiniciar\n🔓 /free - Modo libre\n🔒 /lock - Activar invitaciones")

@bot.on(events.NewMessage(pattern='/reset'))
async def reset(event):
    if event.sender_id != ADMIN_ID: return
    global META_INVITADOS, invitaciones_activas
    try:
        parts = event.text.split()
        if len(parts) > 1: META_INVITADOS = int(parts[1])
    except: pass
    invitaciones_activas = True
    invitaciones.clear()
    try:
        async for member in bot.iter_participants(GRUPO_ID):
            if member.bot or member.id == ADMIN_ID: continue
            uid = str(member.id)
            invitaciones[uid] = 0
            name = member.first_name or "Usuario"
            try: await bot.edit_permissions(GRUPO_ID, member.id, send_messages=False)
            except: pass
            barra = "⬜" * META_INVITADOS
            try:
                await bot.send_message(GRUPO_ID, f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Estás RESTRINGIDO temporalmente.\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos.\n💡 {ENLACE_GRUPO}\n\n📊 Progreso: [{barra}] 0/{META_INVITADOS}")
            except: pass
    except: pass
    guardar_inv()
    await event.reply(f"✅ **Meta: {META_INVITADOS}. {len(invitaciones)} usuarios restringidos.**")

@bot.on(events.NewMessage(pattern='/free'))
async def free(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = False
    invitaciones.clear()
    guardar_inv()
    count = 0
    try:
        async for member in bot.iter_participants(GRUPO_ID):
            if member.bot or member.id == ADMIN_ID: continue
            try:
                await bot.edit_permissions(GRUPO_ID, member.id, send_messages=True)
                count += 1
            except: pass
    except: pass
    await event.reply(f"🔓 **Modo libre. {count} usuarios liberados.**")

@bot.on(events.NewMessage(pattern='/lock'))
async def lock(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = True
    await event.reply("🔒 **Invitaciones activadas.**")

# ============ MOTOR DE BÚSQUEDA ============
@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_search_new(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (m.text or "Archivo").split('\n')[0][:50]
        await bot.send_message(GRUPO, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False)

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_search_edit(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.text and len(m.text) > 20:
        txt = replace_ads(m.text)
        txt = re.sub(r'👋.*?se encontraron', f'👋 **¡Hola {name}!**\n📊 se encontraron', txt)
        if m.id in mirror:
            try:
                await bot.edit_message(chat_id, mirror[m.id], txt[:4000], buttons=make_buttons(m))
            except:
                sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
                mirror[m.id] = sent.id
        else:
            sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
            mirror[m.id] = sent.id

# ============ USUARIOS ============
@bot.on(events.NewMessage)
async def on_user(event):
    if event.out: return
    if event.id in sent_ids: return
    sent_ids.add(event.id)
    if event.is_private and event.sender_id != ADMIN_ID:
        msg = "👋 **¡Hola!**\n\nSolo funciono en el grupo:\n👉 " + GRUPO + "\n\n¡Únete para buscar películas!"
        await event.reply(msg)
        return
    q = event.text.strip() if event.text else ""
    if len(q) < 2 or q.startswith("/") or q.startswith("."): return
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    # Anti-eco: no buscar lo mismo 2 veces seguidas
    last = active.get(uid, {}).get('last_query', '')
    if q == last:
        return
    active[uid] = {'chat': event.chat_id, 'name': name, 'last_query': q}
    mirror.clear()
    await user.send_message(SEARCH_GROUP, f"/search {q}")

@bot.on(events.CallbackQuery)
async def on_click(event):
    data = event.data
    if not data: return
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    active[uid] = {'chat': event.chat_id, 'name': name}
    msgs = await user.get_messages(SEARCH_GROUP, limit=20)
    for m in msgs:
        if m.sender and m.sender.bot and m.buttons:
            for row in m.buttons:
                for btn in row:
                    if btn.data == data:
                        await event.answer("⚡")
                        await btn.click()
                        return
    await event.answer("⏳ Expiró")

# Servidor falso para Render
import threading as _thr
from http.server import HTTPServer as _HS, BaseHTTPRequestHandler as _BH
class _FH(_BH):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
def _start():
    p = int(os.environ.get("PORT", 10000))
    _HS(("0.0.0.0", p), _FH).serve_forever()
_thr.Thread(target=_start, daemon=True).start()

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ @BuddyMovies_Bot - 1 motor")
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

asyncio.run(main())

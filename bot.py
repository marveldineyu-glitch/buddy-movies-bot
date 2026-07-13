import asyncio, re
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
import json, os

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzgBu1WPkV3MOD3nArYQ0CHOcwLwKQL6hLC3pD7Iyny_j5ElbT4W5ctOur32zChqyOjObIwvk3GrjPvNQNt498yQju8tPky5j_JFrdXX1XwfHe6a7SgYGezZEyeElkZsj7SsnPP3vWVsYPnRTVFjFQ2VvJn00QZppNX8QBJc1jQUVVQ8ataL0nkns6RKJFiDMHy1SNW4o9Z2hGtJ8WVGLZBENuyoGmeZNyPik8kOSOc3ScL9fHGNi-cbODAXc23MyI_rp7s4bEtnkAEy0Z50TE0jE4cqksW6RuBqpeAiNI7wYoUqT3twgy_Qxx3rSKYIqWQcGx9XTQWqIHLh20PP2i4Saro="
SEARCH_BOT1 = "@AutoFilter_Robot"
SEARCH_GROUP2 = "@pooppuuui"
SEARCH_BOT3 = "@TlgramMovieSearch_Bot"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
GRUPO_ID = -1002311102965
MI_GRUPO = "@BuddyMovies_canal"
MI_BOT = "@BuddyMovies_Bot"
ADMIN_ID = 7771137226
ENLACE_GRUPO = "https://t.me/BuddyMovies_canal/1088"
META_INVITADOS = 5

bot = TelegramClient('unified_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
active = {}
mirror1, mirror2, mirror3 = {}, {}, {}
mirror_chat = {}
our_msg = {}

invitaciones = {}
invitaciones_activas = False  # Por defecto LIBRE
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
    text = text.replace("@FILM_PARADIZE", MI_GRUPO).replace("@RZXBOTZ", MI_BOT)
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@TlgramMovieSearch_Bot", "@BuddyMovies_Bot")
    text = text.replace("Estrenos 2026", "@BuddyMovies_canal")
    text = re.sub(r"https?://[^\s]*terabox[^\s]*", "", text)
    return text

def clean_caption(text):
    if not text: return ""
    lines = text.split('\n')
    cut = len(lines)
    for i in range(len(lines)-1, -1, -1):
        if ('─' in lines[i] or '━' in lines[i]) and i > 0:
            if i+1 < len(lines) and ('@' in lines[i+1] or '➠' in lines[i+1]):
                cut = i
                break
    return '\n'.join(lines[:cut]).strip()

def make_buttons(msg):
    if not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = []
        for btn in row:
            if btn.url and 'LfvtadGw' in btn.url: continue
            if btn.data:
                t = btn.text.replace('🎞 Quality', '🎞 Resolución').replace('Quality', 'Resolución')
                r.append(Button.inline(t, btn.data))
            elif btn.url:
                r.append(Button.url(btn.text, btn.url))
        if r: btns.append(r)
    return btns

def get_user():
    if not active: return None, None, "Usuario"
    valid = [k for k in active if k is not None]
    if not valid: return None, None, "Usuario"
    uid = valid[-1]
    return uid, active[uid]['chat'], active[uid]['name']

# ============ SISTEMA DE INVITACIONES CORREGIDO ============
@bot.on(events.ChatAction(chats=[GRUPO_ID]))
async def on_join(event):
    # Borrar mensajes de sistema
    try: await event.delete()
    except: pass
    
    if event.user_joined:
        name = event.user.first_name or "Usuario"
        
        # Siempre enviar bienvenida
        welcome = f"🎬 **¡Bienvenido {name} a Buddy Movies!** 🍿\n\n📢 Busca películas y series escribiendo el nombre en el chat.\n\n🔥 Tenemos el mejor motor de búsqueda para encontrar el mejor contenido."
        await bot.send_message(GRUPO_ID, welcome)
        
        if not invitaciones_activas: return  # Modo libre, no restringir
        
        uid = str(event.user.id)
        invitaciones[uid] = 0
        guardar_inv()
        barra = "⬜" * META_INVITADOS
        msg = f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Estás RESTRINGIDO temporalmente.\nPara poder escribir aquí, debes completar la misión.\n\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos al grupo.\n\n💡Si no sabes cómo hacerlo Clic aquí 👇🏻\n{ENLACE_GRUPO}\n\n📊 **TU PROGRESO ACTUAL:**\nProgreso: [{barra}] 0/{META_INVITADOS}\n\n👆 El contador se actualiza solo. ¡Invita y mira cómo sube!"
        await bot.send_message(GRUPO_ID, msg)
    
    if event.user_added:
        # Detectar QUIÉN añadió
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
                        # LIBERAR permisos
                        await bot.edit_permissions(GRUPO_ID, int(inviter_id), send_messages=True)
                    except:
                        name = "Usuario"
                    await bot.send_message(GRUPO_ID, f"🎉 **¡Felicidades {name}!** Completaste la misión. ¡Ya puedes escribir!")

@bot.on(events.NewMessage(chats=[GRUPO_ID]))
async def anti_enlaces(event):
    if event.sender_id == ADMIN_ID: return
    
    # Eliminar enlaces
    if event.text and re.search(r'https?://|t\.me/', event.text):
        await event.delete()
        return
    
    # Bloquear escritura si debe invitar
    uid = str(event.sender_id)
    if uid in invitaciones and invitaciones_activas:
        await event.delete()
        count = invitaciones[uid]
        barra = "🟩" * count + "⬜" * (META_INVITADOS - count)
        try: await bot.send_message(GRUPO_ID, f"⛔ Completa la misión: [{barra}] {count}/{META_INVITADOS}")
        except: pass
        return
    
    # Si no está restringido, dejar pasar (no hacer nada, lo capturará on_user)

# ============ COMANDOS DE ADMIN ============
@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    estado = "🔒 Activado" if invitaciones_activas else "🔓 Desactivado"
    await event.reply(f"""⚙️ **PANEL DE ADMINISTRADOR**

👥 **Estado:** {estado}
📊 **Meta:** {META_INVITADOS} invitados
👤 **Pendientes:** {len(invitaciones)} usuarios

**Comandos:**
🔄 /reset - Reiniciar invitaciones de todos
🔓 /free - Modo libre
🔒 /lock - Activar invitaciones
📊 /meta <numero> - Cambiar meta""")

@bot.on(events.NewMessage(pattern='/reset'))
async def reset(event):
    if event.sender_id != ADMIN_ID: return
    global META_INVITADOS, invitaciones_activas
    try:
        parts = event.text.split()
        if len(parts) > 1:
            META_INVITADOS = int(parts[1])
    except:
        pass
    
    invitaciones_activas = True
    invitaciones.clear()
    
    try:
        async for member in bot.iter_participants(GRUPO_ID):
            if member.bot or member.id == ADMIN_ID: continue
            uid = str(member.id)
            invitaciones[uid] = 0
            name = member.first_name or "Usuario"
            
            # RESTRINGIR permisos de escritura
            try:
                await bot.edit_permissions(GRUPO_ID, member.id, send_messages=False)
            except: pass
            
            barra = "⬜" * META_INVITADOS
            try:
                await bot.send_message(GRUPO_ID, 
                    f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n"
                    f"🔒 Estás RESTRINGIDO temporalmente.\n"
                    f"Para poder escribir aquí, debes completar la misión.\n\n"
                    f"🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos al grupo.\n\n"
                    f"💡Si no sabes cómo hacerlo Clic aquí 👇🏻\n{ENLACE_GRUPO}\n\n"
                    f"📊 **TU PROGRESO ACTUAL:**\n"
                    f"Progreso: [{barra}] 0/{META_INVITADOS}\n\n"
                    f"👆 El contador se actualiza solo. ¡Invita y mira cómo sube!")
            except: pass
    except Exception as e:
        print(f"Error: {e}")
    
    guardar_inv()
    await event.reply(f"✅ **Reset completado. Meta: {META_INVITADOS}. {len(invitaciones)} usuarios restringidos.**")

@bot.on(events.NewMessage(pattern='/free'))
async def free(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = False
    invitaciones.clear()
    guardar_inv()
    
    # Liberar a TODOS
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
    await event.reply("🔒 **Invitaciones activadas.** Nuevos usuarios deberán invitar.")

@bot.on(events.NewMessage(pattern='/meta'))
async def meta(event):
    if event.sender_id != ADMIN_ID: return
    try:
        nueva = int(event.text.split()[1])
        global META_INVITADOS
        META_INVITADOS = nueva
        await event.reply(f"📊 **Meta: {nueva} invitados.**")
    except:
        await event.reply("❌ /meta <numero>")

# ============ MOTORES DE BÚSQUEDA ============
@user.on(events.NewMessage(chats=SEARCH_BOT1))
async def on_bot1(event):
    m = event.message
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text:
        if any(x in m.text.lower() for x in ["save the file", "will be deleted", "select language"]): return
        if "no results found" in m.text.lower() or "not available" in m.text.lower():
            await bot.send_message(chat_id, SIN_RESULTADOS)
            return
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = clean_caption(raw).split('\n')[0] or "Archivo"
        await bot.send_message(GRUPO, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False)
        return
    if m.text and len(m.text) > 20:
        txt = replace_ads(m.text)
        txt = re.sub(r'Hey \*\*.*?\*\*!', f'👋 **¡Hola {name}!**', txt)
        txt = re.sub(r'Search Query:', '🔍 Búsqueda:', txt)
        txt = re.sub(r'Total Results:', '📊 Resultados:', txt)
        txt = re.sub(r'Page:', '📄 Página:', txt)
        txt = re.sub(r'Tap on the file button and then start to download', 'Presiona el archivo para descargar', txt)
        sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
        mirror1[m.id] = sent.id
        mirror_chat[m.id] = chat_id

@user.on(events.MessageEdited(chats=SEARCH_BOT1))
async def on_bot1_edit(event):
    m = event.message
    if m.id in mirror1:
        uid, chat_id, name = get_user()
        if uid:
            try:
                txt = replace_ads(m.text)
                txt = re.sub(r'Hey \*\*.*?\*\*!', f'👋 **¡Hola {name}!**', txt)
                txt = re.sub(r'Search Query:', '🔍 Búsqueda:', txt)
                txt = re.sub(r'Total Results:', '📊 Resultados:', txt)
                txt = re.sub(r'Page:', '📄 Página:', txt)
                await bot.edit_message(chat_id, mirror1[m.id], txt[:4000], buttons=make_buttons(m))
            except: pass

@user.on(events.NewMessage(chats=SEARCH_GROUP2))
async def on_bot2_new(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = clean_caption(raw).split('\n')[0] or "Archivo"
        await bot.send_message(GRUPO, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False)

@user.on(events.MessageEdited(chats=SEARCH_GROUP2))
async def on_bot2_edit(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    uid, chat_id, name = get_user()
    if not uid: return
    if m.text and any(x in m.text.lower() for x in ["buscando", "espera", "recuerda usar", "ayúdanos", "compártelo", "gracias"]): return
    if m.text and len(m.text) > 20:
        txt = replace_ads(m.text)
        txt = re.sub(r'👋.*?se encontraron', f'👋 **¡Hola {name}!**\n📊 se encontraron', txt)
        if m.id in mirror2:
            try:
                await bot.edit_message(chat_id, mirror2[m.id], txt[:4000], buttons=make_buttons(m))
            except:
                sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
                mirror2[m.id] = sent.id
        else:
            sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
            mirror2[m.id] = sent.id

@user.on(events.NewMessage(chats=SEARCH_BOT3))
async def on_bot3(event):
    m = event.message
    uid, chat_id, name = get_user()
    if not uid: return
    
    if m.media:
        raw = replace_ads(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        title = (m.text or "Archivo").split('\n')[0]
        await bot.send_message(GRUPO, f"🎬 **Aquí tienes {name}**\n\n📁 **{title}**", buttons=[[Button.url("🎥 VER CONTENIDO", link)]], link_preview=False)
        return
    
    if not m.text: return
    if any(x in m.text.lower() for x in ["maldito", "comparte", "terabox", "revisa el anuncio", "no te lo guardes"]): return
    
    txt = replace_ads(m.text)
    if uid in our_msg:
        try:
            await bot.edit_message(chat_id, our_msg[uid], txt[:4000], buttons=make_buttons(m))
            mirror3[m.id] = our_msg[uid]
            return
        except:
            pass
    
    sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
    our_msg[uid] = sent.id
    mirror3[m.id] = sent.id

@user.on(events.MessageEdited(chats=SEARCH_BOT3))
async def on_bot3_edit(event):
    m = event.message
    if m.id in mirror3:
        uid, chat_id, name = get_user()
        if uid:
            try:
                await bot.edit_message(chat_id, mirror3[m.id], replace_ads(m.text)[:4000], buttons=make_buttons(m))
            except: pass

# ============ USUARIOS ============
@bot.on(events.NewMessage)
async def on_user(event):
    if event.is_private and event.sender_id != ADMIN_ID:
        msg = "👋 **¡Hola!**\n\nSolo funciono en el grupo:\n👉 " + GRUPO + "\n\n¡Únete para buscar películas!"
        await event.reply(msg)
        return
    if event.out: return  # Ignorar mensajes del propio bot
    q = event.text.strip() if event.text else ""
    if len(q) < 2 or q.startswith("/") or q.startswith("."): return
    uid = event.sender_id or event.chat_id
    try:
        sender = await bot.get_entity(uid)
        name = sender.first_name or "Usuario"
    except:
        name = "Usuario"
    active[uid] = {'chat': event.chat_id, 'name': name}
    mirror1.clear(); mirror2.clear(); mirror3.clear()
    our_msg.pop(uid, None)
    await user.send_message(SEARCH_BOT1, q)
    await user.send_message(SEARCH_GROUP2, f"/search {q}")
    await user.send_message(SEARCH_BOT3, q)

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
    for chat in [SEARCH_BOT1, SEARCH_GROUP2, SEARCH_BOT3]:
        msgs = await user.get_messages(chat, limit=20)
        for m in msgs:
            if m.buttons:
                for row in m.buttons:
                    for btn in row:
                        if btn.data == data:
                            await event.answer("⚡")
                            await btn.click()
                            return
    await event.answer("⏳ Expiró")

# Servidor falso para Render
import threading as _thr, os as _os
from http.server import HTTPServer as _HS, BaseHTTPRequestHandler as _BH
class _FH(_BH):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
def _start():
    p = int(_os.environ.get("PORT", 10000))
    print(f"🔌 Puerto {p}")
    _HS(("0.0.0.0", p), _FH).serve_forever()
_thr.Thread(target=_start, daemon=True).start()
print("✅ HTTP OK")

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ @PelisPlay_yabot - Completo")
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

asyncio.run(main())

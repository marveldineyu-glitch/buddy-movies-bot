import asyncio, re, json, os
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION = "1AZWarzQBuyuVqdCO0U8mVphUrO9MIarehdGQ0eauLUkQH2NKreBY40FDz3IFDT9-0sFGhdH_9GSRpvTyUt6JV2Fv71zV0qkO-b25JRR8q9gZz34BAHTO8fhTBGwdSUdg2xZhMSUsVLuZmrprBDKL-8hVtHL4HuveZFeZA3c2rKTT187WYnC9UyKz4acDHEutpulV6IEJFBFXMFzAsLT5Th0kwwgwBTN0_rb3CUMEjvvwF_s7SBQpOwwzQjHsDAgh9eJ39wZauYzgTYMiIzoHwZWUQ6CmERXiw2WKnggO_R5cf7EcgEfwaTwR_H76HT7ORKTNBgXhzOW0SzSw59HakA2AdU_DLL0="
SEARCH_BOT1 = "@AutoFilter_Robot"
SEARCH_GROUP2 = "@pooppuuui"
SEARCH_BOT3 = "@TlgramMovieSearch_Bot"
CANAL = "@BuddyMovies_canal"
GRUPO = "@BuddyMovies_official"
GRUPO_ID = 2311102965
ADMIN_ID = 7771137226
ENLACE_GRUPO = "https://t.me/BuddyMovies_official/1088"
META_INVITADOS = 5

bot = TelegramClient('buddy_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
active = {}
mirror1, mirror2, mirror3 = {}, {}, {}
mirror_chat = {}
our_msg = {}

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
    text = text.replace("@FILM_PARADIZE", MI_GRUPO).replace("@RZXBOTZ", MI_BOT)
    text = text.replace("@TlgramMovieGroup_Bot", "@BuddyMovies_Bot")
    text = text.replace("@TlgramMovieSearch_Bot", "@BuddyMovies_Bot")
    text = text.replace("Estrenos 2026", "@BuddyMovies_canal")
    text = re.sub(r"https?://[^\s]*terabox[^\s]*", "", text)
    return text

MI_GRUPO = "@BuddyMovies_official"
MI_BOT = "@BuddyMovies_Bot"

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

# ============ INVITACIONES ============
@bot.on(events.ChatAction(chats=[GRUPO_ID]))
async def on_join(event):
    try: await event.delete()
    except: pass
    
    if event.user_joined:
        name = event.user.first_name or "Usuario"
        await bot.send_message(GRUPO_ID, f"🎬 **¡Bienvenido {name} a Buddy Movies!** 🍿\n\n📢 Busca películas y series escribiendo el nombre en el chat.\n\n🔥 Tenemos el mejor motor de búsqueda para encontrar el mejor contenido.")
        
        if not invitaciones_activas: return
        uid = str(event.user.id)
        invitaciones[uid] = 0
        guardar_inv()
        barra = "⬜" * META_INVITADOS
        await bot.send_message(GRUPO_ID, f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 Estás RESTRINGIDO temporalmente.\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos.\n💡 {ENLACE_GRUPO}\n\n📊 Progreso: [{barra}] 0/{META_INVITADOS}")
    
    if event.user_added and event.action_message and event.action_message.from_id:
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
                except: name = "Usuario"
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

# ============ COMANDOS ADMIN ============
@bot.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id != ADMIN_ID: return
    estado = "🔒 Activado" if invitaciones_activas else "🔓 Desactivado"
    await event.reply(f"⚙️ **PANEL**\n👥 {estado}\n📊 Meta: {META_INVITADOS}\n👤 Pendientes: {len(invitaciones)}\n\n🔄 /reset <num>\n🔓 /free\n🔒 /lock")

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
            try: await bot.edit_permissions(GRUPO_ID, member.id, send_messages=False)
            except: pass
            barra = "⬜" * META_INVITADOS
            try: await bot.send_message(GRUPO_ID, f"🛑 **¡ATENCIÓN {member.first_name}!** 🛑\n\n🔒 Estás RESTRINGIDO.\n🎯 Añade a {META_INVITADOS} amigos.\n💡 {ENLACE_GRUPO}\n\n📊 [{barra}] 0/{META_INVITADOS}")
            except: pass
    except: pass
    guardar_inv()
    await event.reply(f"✅ Meta: {META_INVITADOS}. {len(invitaciones)} restringidos.")

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
    await event.reply(f"🔓 {count} liberados.")

@bot.on(events.NewMessage(pattern='/lock'))
async def lock(event):
    if event.sender_id != ADMIN_ID: return
    global invitaciones_activas
    invitaciones_activas = True
    await event.reply("🔒 Activado.")

# ============ BOT 1: @AutoFilter_Robot ============
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

# ============ BOT 2: @TlgramMovieGroup_Bot ============
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
        if m.id in mirror2:
            try:
                await bot.edit_message(chat_id, mirror2[m.id], txt[:4000], buttons=make_buttons(m))
            except:
                sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
                mirror2[m.id] = sent.id
        else:
            sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
            mirror2[m.id] = sent.id

# ============ BOT 3: @TlgramMovieSearch_Bot ============
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
    if event.chat_id == GRUPO_ID: return
    if event.out: return
    if event.is_private and event.sender_id != ADMIN_ID:
        await event.reply(f"👋 **¡Hola!**\n\nSolo funciono en el grupo:\n👉 {GRUPO}\n\n¡Únete para buscar películas!")
        return
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

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ 3 motores - @BuddyMovies_Bot")
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

asyncio.run(main())

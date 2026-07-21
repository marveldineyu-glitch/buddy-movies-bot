import asyncio, gc, os, threading
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from http.server import HTTPServer, BaseHTTPRequestHandler

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "7812301734:AAHIXx70G83tb41pBczdCcdhHRiBlz43g7A"
SESSION = "1AZWarzYBu72KHN1Z6-0Q0I9KI7JSZ_3dpMTSuiN6aNsb_STMDHX10-fo09zyXAOhbRSHE0gJJlFU3iRYuqPMAu_U_ka8RuHU98KFxMVTOGWZrilLGBsZSUirNT1C4-8Q4Po3XX_kWI_6GSCEc_pRBgCktyuzZL4rSXwKlCSpx1-NmSqQ-Vb62e47hKUznQugDB31Sl71tM7-3MLMp3EmqbIA_m5f6zA2gZYX4swtE0aCw1Su8neeah5rGTQI7imOISQZRNgStTrmcmBtmUVVPmzqM6-b512Np3cLBv5vIMBchTwqB77ipLEj-xHhdB8hdIPPJtvo9aqQBtZv_faUy-PrhAeiNmo="
SEARCH_GROUP = "@pooppuuui"
CANAL = "@BuddyMovies_canal"
GRUPO = "@mabu205"

bot = TelegramClient('simple_bot', API_ID, API_HASH)
user = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# Cola de usuarios para multi-usuario
queue = []
mirror = {}
mirror_chat = {}

def clean_text(text):
    if not text: return text
    text = text.replace('@MotorBusquedaBot', '@BuddyMovies_Bot')
    text = text.replace('@TlgramMovieGroup_Bot', '@BuddyMovies_Bot')
    text = text.replace('Estrenos 2026', '@BuddyMovies_official')
    text = text.replace('🔗 Estrenos 2026', '🔗 @BuddyMovies_official')
    return text

def make_buttons(msg):
    if not msg.buttons: return None
    btns = []
    for row in msg.buttons:
        r = [Button.inline(btn.text, btn.data) if btn.data else Button.url(btn.text, btn.url) for btn in row]
        btns.append(r)
    return btns

@user.on(events.NewMessage(chats=SEARCH_GROUP))
async def on_result(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    
    # Auto-click
    if m.text and "selecciona un método" in m.text.lower() and m.buttons:
        await m.buttons[0][0].click()
        return
    if m.text and "selecciona un almac" in m.text.lower() and m.buttons:
        await m.buttons[0][0].click()
        return
    if m.text and any(x in m.text.lower() for x in ["maldito", "comparte", "revisa el anuncio", "espera mientras", "procesando"]):
        return
    
    chat_id = queue[0] if queue else GRUPO
    
    if m.media:
        raw = clean_text(m.text or "")
        sent = await user.send_file(CANAL, m.media, caption=raw)
        link = f"https://t.me/{CANAL[1:]}/{sent.id}"
        await bot.send_message(chat_id, f"🎬 **Aquí tienes**\n\n📁 {raw.split(chr(10))[0] if raw else 'Archivo'}\n\n🔗 {link}", buttons=[[Button.url("🎥 VER", link)]])
        if queue: queue.pop(0)

@user.on(events.MessageEdited(chats=SEARCH_GROUP))
async def on_edit(event):
    m = event.message
    if not m.sender or not m.sender.bot: return
    if not m.text: return
    if "buscando" in m.text.lower() or "espera" in m.text.lower(): return
    
    chat_id = queue[0] if queue else GRUPO
    txt = clean_text(m.text)
    
    if m.id in mirror:
        try:
            await bot.edit_message(mirror_chat[m.id], mirror[m.id], txt[:4000], buttons=make_buttons(m))
            return
        except: pass
    sent = await bot.send_message(chat_id, txt[:4000], buttons=make_buttons(m))
    mirror[m.id] = sent.id
    mirror_chat[m.id] = chat_id

@bot.on(events.NewMessage)
async def on_msg(event):
    if event.out or not event.text: return
    q = event.text.strip()
    if len(q) < 2 or q.startswith("/"): return
    queue.append(event.chat_id)
    await user.send_message(SEARCH_GROUP, f"/search {q}")
    gc.collect()

async def main():
    await user.start()
    await bot.start(bot_token=BOT_TOKEN)
    print("✅ Bridge listo")
    await asyncio.gather(bot.run_until_disconnected(), user.run_until_disconnected())

class H(BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    def do_HEAD(self): self.send_response(200); self.end_headers()
def s(): HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 10000))), H).serve_forever()
threading.Thread(target=s, daemon=True).start()

asyncio.run(main())

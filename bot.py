import asyncio, logging, time, re, json, os, hashlib, pickle
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION_STRING_USER = "1AZWarzMBu6BrSOlyonpA0yEiqthxRnoxDySaJWVuf1jzmC9tgBbNrh8UEzm6Xn42_1YSj5WRTc3CKgJNcZz6Q77gM9Jl5TPNfEBOu4wj9P4l-DvjM6Kbr4hW5NCRNsQXGXaJwZL4tLbII-PEbYwsCt1sQ3dAZZD1GW5wDKN7A0eIziwOz2zX8uEFx_LpLQXjU2fAulMgtjGTFWOqkv-Xl3S_seDYrOY14ElP3k4qVqrYLgeVkcbqVOpmul3iJ5IyrRg1zloCfDH8PAsoTR-kgqsYE4_9MpcpFIExkUmCG-FX7Ik849KzTci2WpZ4Qkp7oM1qvDCfGtEobRO9BlAdJYGmo2hVHeE="

ADMIN_ID = 7771137226
ALLOWED_GROUP = "BuddyMovies_official"
ENLACE_GRUPO = "https://t.me/BuddyMovies_official"
META_INVITADOS = 5
RESULTS_PER_PAGE = 10
TUTORIAL_LINK = "https://t.me/BuddyMovies_official/480"
TARGET_CHANNELS = ["@SeriesbyJoel", "@chatpeliculasymas", "@Almacen_Pelis", "@mundoword39", "@Neoanimes", "@AnimeLatinoHD", "@tiyiot"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BuddyMoviesBot:
    def __init__(self):
        self.bot = None; self.user = None
        self.idx = defaultdict(list)
        self.titles = {}
        self.ready = False; self.ecache = {}
        self.searches = {}
        self.pending = {}
        self.pfile = "usuarios_invitacion.json"
        self.channels_file = "canales_guardados.json"
        self.additional_channels = []
        try:
            if os.path.exists(self.pfile):
                with open(self.pfile) as f: self.pending = json.load(f)
        except: pass
        try:
            if os.path.exists(self.channels_file):
                with open(self.channels_file) as f:
                    self.additional_channels = json.load(f).get('additional_channels', [])
        except: pass
        try:
            if os.path.exists("video_index.pkl"):
                with open("video_index.pkl",'rb') as f:
                    d = pickle.load(f)
                    for k,ms in d.get('content_index',{}).items(): self.idx[k] = ms
                    self.titles = d.get('title_index',{})
                    self.ecache = d.get('entity_cache',{})
                self.ready = True
        except: pass

    def _save_pending(self):
        try: json.dump(self.pending, open(self.pfile,'w'))
        except: pass

    def _save_channels(self):
        try: json.dump({'additional_channels': self.additional_channels}, open(self.channels_file,'w'))
        except: pass

    def _total(self):
        u = set()
        for ms in self.idx.values():
            for m in ms: u.add(f"{m['entity_name']}_{m['message_id']}")
        return len(u)

    async def _search(self, q):
        if not self.ready: return []
        q_lower = q.lower().strip()
        r, s = [], set()
        for md in self.titles.values():
            if q_lower in md.get('clean_title','').lower():
                uid = f"{md['entity_name']}_{md['message_id']}"
                if uid not in s: r.append(md); s.add(uid)
        if not r:
            qw = [w for w in re.findall(r'\b\w+\b', q_lower) if len(w)>1]
            for w in qw:
                if w in self.idx:
                    for md in self.idx[w]:
                        uid = f"{md['entity_name']}_{md['message_id']}"
                        if uid not in s: r.append(md); s.add(uid)
        return r

    def _create_buttons(self, results, page):
        total = len(results)
        total_pages = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
        if page >= total_pages: page = 0
        start = page * RESULTS_PER_PAGE
        end = min(start + RESULTS_PER_PAGE, total)
        page_results = results[start:end]
        btns = []
        for i, r in enumerate(page_results):
            btns.append([Button.inline(r['clean_title'][:50], f"send_{start+i}")])
        nav = []
        if total_pages > 1:
            if page > 0:
                nav.append(Button.inline("⬅️", f"page_{page-1}"))
            nav.append(Button.inline(f"{page+1}/{total_pages}", "noop"))
            if page < total_pages - 1:
                nav.append(Button.inline("➡️", f"page_{page+1}"))
            btns.append(nav)
        return btns

    async def _restrict(self, uid):
        try:
            await self.bot(EditBannedRequest(
                ALLOWED_GROUP, uid,
                ChatBannedRights(until_date=None, send_messages=True)
            ))
        except: pass

    async def _unrestrict(self, uid):
        try:
            await self.bot(EditBannedRequest(
                ALLOWED_GROUP, uid,
                ChatBannedRights(until_date=None, send_messages=False)
            ))
        except: pass

    def _setup_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start(ev):
            await ev.reply(f"🎬 **@BuddyMovies_Bot** ⚡\n📊 **{self._total()} videos**\n🔍 Escribe lo que buscas")

        @self.bot.on(events.NewMessage(pattern='/addchannel'))
        async def addch(ev):
            if ev.sender_id != ADMIN_ID: return
            text = ev.message.text.replace('/addchannel', '').strip()
            # Dividir por espacios o saltos de línea
            channels = text.replace('\n', ' ').split()
            added = []
            for ch in channels:
                if not ch.startswith('@'): continue
                if ch in self.additional_channels:
                    added.append(f"❌ {ch} ya existe")
                    continue
                try:
                    ent = await self.user.get_entity(ch)
                    self.ecache[ch] = {'id': ent.id, 'username': getattr(ent, 'username', None)}
                    self.additional_channels.append(ch)
                    self._save_channels()
                    count = 0
                    async for m in self.user.iter_messages(ent, limit=10000):
                        if await self._is_video(m):
                            await self._index(m, ch); count += 1
                    self.ready = True
                    added.append(f"✅ {ch} - {count} videos")
                except Exception as e:
                    added.append(f"❌ {ch}: {str(e)[:50]}")
            await ev.reply('\n'.join(added) if added else "❌ Sin canales válidos")

        @self.bot.on(events.ChatAction)
        async def on_chat_action(ev):
            if ev.user_joined or ev.user_added or ev.user_left or ev.user_kicked:
                try: await ev.delete()
                except: pass
            
            if ev.user_joined:
                uid = str(ev.user.id)
                user = ev.user
                name = user.first_name or "Usuario"
                welcome = f"🎬 **Bienvenido {name} a Buddy Movies**\n\n**Descubre tu próxima obsesión:**\n🎥 Películas • 🐉 Anime • 📺 Series\n💕 Doramas • 📖 Novelas • ✨ Dibujos\n🍿 Estrenos • 🎭 TV\n\n**👇 Encuentra al instante:**\n🔥 Lo nuevo • 🌟 Recomendaciones para ti\n🔍 Búsqueda rápida • 📰 Noticias\n\n**Tu mundo de entretenimiento en un solo lugar**"
                sent = await ev.reply(welcome)
                self.pending[uid] = {"count": 0, "name": name, "welcome_msg_id": sent.id, "progress_msg_id": None}
                self._save_pending()
            
            if ev.user_added:
                inviter = None
                if hasattr(ev, 'action_message') and ev.action_message:
                    am = ev.action_message
                    if hasattr(am, 'from_id') and am.from_id:
                        try: inviter = str(am.from_id.user_id)
                        except: pass
                if inviter and inviter in self.pending:
                    data = self.pending[inviter]
                    data["count"] = data.get("count", 0) + 1
                    count = data["count"]
                    if count >= META_INVITADOS:
                        await self._unrestrict(int(inviter))
                        try:
                            mids = []
                            if data.get("welcome_msg_id"): mids.append(data["welcome_msg_id"])
                            if data.get("progress_msg_id"): mids.append(data["progress_msg_id"])
                            if mids: await self.bot.delete_messages(ALLOWED_GROUP, mids)
                        except: pass
                        await self.bot.send_message(ALLOWED_GROUP, f"🎉 **¡Felicidades {data['name']}!** Completaste la misión. ¡Ya puedes escribir!")
                        del self.pending[inviter]
                    else:
                        if data.get("progress_msg_id"):
                            try:
                                barra = "🟩" * count + "⬜" * (META_INVITADOS - count)
                                await self.bot.edit_message(ALLOWED_GROUP, data["progress_msg_id"], f"📊 **TU PROGRESO ACTUAL:**\nProgreso: [{barra}] {count}/{META_INVITADOS}\n\n👆 ¡Invita y mira cómo sube!")
                            except: pass
                    self._save_pending()
                uid = str(ev.user.id)
                if uid not in self.pending:
                    user = ev.user
                    self.pending[uid] = {"count": 0, "name": user.first_name or "Usuario", "welcome_msg_id": None, "progress_msg_id": None}
                    self._save_pending()

        @self.bot.on(events.NewMessage)
        async def handle(ev):
            if ev.out: return
            uid = str(ev.sender_id)
            if not ev.is_private and uid in self.pending and ev.sender_id != ADMIN_ID:
                await ev.delete()
                await self._restrict(ev.sender_id)
                user = ev.sender
                name = user.first_name or "Usuario"
                data = self.pending[uid]
                count = data.get("count", 0)
                barra = "🟩" * count + "⬜" * (META_INVITADOS - count)
                msg = f"🛑 **¡ATENCIÓN {name}!** 🛑\n\n🔒 **Estás RESTRINGIDO temporalmente.**\nPara poder escribir aquí, debes completar la misión.\n\n🎯 **MISIÓN:** Añade a {META_INVITADOS} amigos al grupo.\n\n💡Si no sabes cómo hacerlo Clic aquí 👇🏻\n{TUTORIAL_LINK}\n\n📊 **TU PROGRESO ACTUAL:**\nProgreso: [{barra}] {count}/{META_INVITADOS}\n\n👆 El contador se actualiza solo. ¡Invita y mira cómo sube!"
                sent = await ev.reply(msg, link_preview=False)
                self.pending[uid]["progress_msg_id"] = sent.id
                self._save_pending()
                return
            if ev.text and ev.text.startswith('/'): return
            if ev.is_private and ev.sender_id != ADMIN_ID:
                await ev.reply(f"👋 ¡Hola!\n\n🔍 Soy @BuddyMovies_Bot\n👉 Únete: {ENLACE_GRUPO}", link_preview=False)
                return
            q = ev.text.strip() if ev.text else ""
            if len(q) < 2: return
            results = await self._search(q)
            if results:
                self.searches[ev.sender_id] = {"results": results, "query": q}
                btns = self._create_buttons(results, 0)
                total = len(results)
                tp = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
                await ev.reply(f"🔍 **{q}**\n📊 {total} resultados • Página 1/{tp}\n👇 Selecciona:", buttons=btns)
            else:
                await ev.reply(f"❌ Sin resultados para: `{q}`")

        @self.bot.on(events.CallbackQuery(pattern=rb'^page_(\d+)$'))
        async def page_callback(ev):
            try:
                page = int(ev.data.decode().split('_')[1])
                user_data = self.searches.get(ev.sender_id, {})
                results = user_data.get("results", [])
                if not results: await ev.answer("❌ Búsqueda expirada"); return
                btns = self._create_buttons(results, page)
                await ev.edit(buttons=btns)
                total = len(results)
                tp = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
                await ev.answer(f"Página {page+1}/{tp}")
            except: await ev.answer("❌ Error")

        @self.bot.on(events.CallbackQuery(pattern=rb'^send_(\d+)$'))
        async def send_content(ev):
            try:
                idx = int(ev.data.decode().split('_')[1])
                user_data = self.searches.get(ev.sender_id, {})
                results = user_data.get("results", [])
                if idx < len(results):
                    r = results[idx]
                    uname = r.get('username','') or self.ecache.get(r['entity_name'],{}).get('username','')
                    if uname: link = f"https://t.me/{uname}/{r['message_id']}"
                    else: link = f"https://t.me/c/{self.ecache.get(r['entity_name'],{}).get('id',r['entity_name'])}/{r['message_id']}"
                    await ev.respond(f"🎬 ➠ {r['clean_title']}\n\n🔗 [ENLACE DIRECTO]({link})\n⚡ @BuddyMovies_Bot", link_preview=True)
                await ev.answer("✅ Enviado!")
            except: await ev.answer("❌ Error")

    async def _is_video(self, m):
        if not m or not m.media: return False
        try:
            if hasattr(m.media,'document'):
                d = m.media.document
                if hasattr(d,'mime_type') and d.mime_type and d.mime_type.startswith('video/'): return True
                for a in d.attributes:
                    if hasattr(a,'video') and a.video: return True
            return hasattr(m.media,'video')
        except: return False

    def _clean(self, t):
        if not t: return "Sin título"
        t = re.sub(r'https?://\S+','',t); t = re.sub(r'@\w+','',t)
        for l in t.split('\n'):
            c = l.strip()
            if 3<=len(c.split())<=15 and len(c)>10: return c
        return t.strip() or "Sin título"

    async def _index(self, m, e):
        try:
            txt = m.text or m.caption or ''
            if not txt: return
            ct = self._clean(txt)
            words = re.findall(r'\b[a-zA-Z0-9]+\b', ct.lower())
            stop = {'de','la','el','y','en','con','para','por','un','una','hd','full','4k','1080p','720p','latino','español','subtitulado','the','and','with','for','www','com'}
            kw = [w for w in words if w not in stop and len(w)>2]
            uname = self.ecache.get(e,{}).get('username','')
            md = {'channel':e,'clean_title':ct,'message_id':m.id,'entity_name':e,'username':uname}
            for k in set(kw): self.idx[k].append(md)
            self.titles[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
        except: pass

    async def start(self):
        print("🚀 @BuddyMovies_Bot...")
        self.user = TelegramClient(session=StringSession(SESSION_STRING_USER), api_id=API_ID, api_hash=API_HASH)
        await self.user.start()
        self.bot = TelegramClient("bot_final2", API_ID, API_HASH)
        await self.bot.start(bot_token=BOT_TOKEN)
        me = await self.bot.get_me()
        print(f"✅ Bot: @{me.username}")
        self._setup_handlers()
        print(f"🎯 {self._total()} VIDEOS")
        await self.bot.run_until_disconnected()

if __name__ == '__main__':
    bot = BuddyMoviesBot()
    try: asyncio.run(bot.start())
    except KeyboardInterrupt: print("👋 Bot detenido")
    except Exception as e: print(f"❌ Error: {e}"); time.sleep(30); asyncio.run(bot.start())

# GUARDAR ÍNDICE AL FINAL
import atexit
@atexit.register
def save_on_exit():
    try:
        import pickle, json
        sc = {}
        for k, ms in bot.idx.items():
            sc[k] = [{'channel':m['channel'],'clean_title':m['clean_title'],'message_id':m['message_id'],'entity_name':m['entity_name'],'username':m.get('username','')} for m in ms]
        pickle.dump({'content_index':sc,'title_index':bot.tidx,'entity_cache':bot.ecache}, open("video_index.pkl",'wb'))
        json.dump({'additional_channels':bot.additional_channels}, open("canales_guardados.json",'w'))
        json.dump(bot.pending, open("usuarios_invitacion.json",'w'))
        print("💾 Datos guardados")
    except: pass

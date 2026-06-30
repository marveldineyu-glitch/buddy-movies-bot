import asyncio, logging, time, re, json, os, hashlib, pickle
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION_STRING_USER = "1AZWarzQBu4JtB60pYeeTBFlwqbLPYLlRbCp4YsNhVrZR6jWk4ot18CG8GlGC4RtNtPdjbiRH1R38ojZD15V92q59-fr6PQaI8vfZF3iPKWQBVd_NYiHmXCi1haKN93WIilyNs__N79xtn6PfVFselPE_-iGqe3u7f4iierM_HtI13E-Y55DE71wPqqtbYRHC7zk2Hy2u87Kmpr8AOiozvGSUkjvKkWjuk0kiyOrN_heBNMzUTcTV9KQLxlJHelBmFq4MGt1oWpcii2cw6s9i8YDp3CYml_iyhQu_LpDHV38rsB352SaAstITawup8VbtaH4ZKvyAFcs0wYV3dc4GMN0Efybz618="

ADMIN_ID = 7771137226
ALLOWED_GROUP = "BuddyMovies_official"
ENLACE_GRUPO = "https://t.me/BuddyMovies_official"
RESULTS_PER_PAGE = 10
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
        self.restricted_msg = {}
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
            parts = ev.text.split()
            if len(parts) != 2: await ev.reply("❌ /addchannel @canal"); return
            ch = parts[1]
            try:
                ent = await self.user.get_entity(ch)
                self.ecache[ch] = {'id': ent.id, 'username': getattr(ent, 'username', None)}
                self.additional_channels.append(ch)
                self._save_channels()
                count = 0
                async for m in self.user.iter_messages(ent, limit=2000):
                    if await self._is_video(m):
                        await self._index(m, ch); count += 1
                self.ready = True
                await ev.reply(f"✅ {ch} - {count} videos")
            except Exception as e: await ev.reply(f"❌ Error: {e}")

        @self.bot.on(events.ChatAction)
        async def on_chat_action(ev):
            if ev.user_joined or ev.user_added or ev.user_left or ev.user_kicked:
                try: await ev.delete()
                except: pass
            
            if ev.user_added:
                inviter = None
                if hasattr(ev, 'action_message') and ev.action_message:
                    if hasattr(ev.action_message, 'from_id') and ev.action_message.from_id:
                        try: inviter = str(ev.action_message.from_id.user_id)
                        except: pass
                if inviter and inviter in self.pending:
                    self.pending[inviter] = self.pending.get(inviter, 0) + 1
                    if self.pending[inviter] >= 1:
                        await self._unrestrict(int(inviter))
                        del self.pending[inviter]
                        self._save_pending()
                        if inviter in self.restricted_msg:
                            try: await self.bot.delete_messages(ALLOWED_GROUP, self.restricted_msg[inviter])
                            except: pass
                            del self.restricted_msg[inviter]
                        await self.bot.send_message(ALLOWED_GROUP, "✅ ¡Ya puedes escribir!")
                uid = str(ev.user.id)
                if uid not in self.pending:
                    self.pending[uid] = 0
                    self._save_pending()
            elif ev.user_joined:
                uid = str(ev.user.id)
                if uid not in self.pending:
                    self.pending[uid] = 0
                    self._save_pending()

        @self.bot.on(events.NewMessage)
        async def handle(ev):
            if ev.out: return
            uid = str(ev.sender_id)
            
            if not ev.is_private and uid in self.pending and ev.sender_id != ADMIN_ID:
                await ev.delete()
                await self._restrict(ev.sender_id)
                msg = await ev.reply(f"🛑 Añade a 1 amigo para escribir.\n📎 {ENLACE_GRUPO}", link_preview=False)
                self.restricted_msg[uid] = msg.id
                return
            
            if ev.text and ev.text.startswith('/'): return
            
            if ev.is_private and ev.sender_id != ADMIN_ID:
                await ev.reply(f"👋 ¡Hola!\n\n🔍 Soy @BuddyMovies_Bot\n👉 Únete: {ENLACE_GRUPO}", link_preview=False)
                return
            
            q = ev.text.strip() if ev.text else ""
            if len(q) < 2: return
            
            results = await self._search(q)
            if results:
                self.searches[ev.sender_id] = results
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
                results = self.searches.get(ev.sender_id, [])
                if not results: await ev.answer("❌ Búsqueda expirada"); return
                btns = self._create_buttons(results, page)
                await ev.edit(buttons=btns)
                total = len(results)
                tp = max(1, (total + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
                await ev.answer(f"Página {page+1}/{tp}")
            except Exception as e:
                print(f"Page error: {e}")
                await ev.answer("❌ Error")

        @self.bot.on(events.CallbackQuery(pattern=rb'^send_(\d+)$'))
        async def send_content(ev):
            try:
                idx = int(ev.data.decode().split('_')[1])
                results = self.searches.get(ev.sender_id, [])
                if idx < len(results):
                    r = results[idx]
                    uname = r.get('username','') or self.ecache.get(r['entity_name'],{}).get('username','')
                    if uname:
                        link = f"https://t.me/{uname}/{r['message_id']}"
                    else:
                        eid = self.ecache.get(r['entity_name'],{}).get('id', r['entity_name'])
                        link = f"https://t.me/c/{eid}/{r['message_id']}"
                    await ev.respond(f"🎬 ➠ {r['clean_title']}\n\n🔗 [ENLACE DIRECTO]({link})\n⚡ @BuddyMovies_Bot", link_preview=True)
                await ev.answer("✅ Enviado!")
            except Exception as e:
                print(f"ERROR: {e}")
                await ev.answer("❌ Error")

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
        self.bot = TelegramClient("bot_v14", API_ID, API_HASH)
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

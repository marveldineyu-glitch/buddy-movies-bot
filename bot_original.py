import asyncio, logging, time, re, json, os, hashlib, pickle
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession

API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"
SESSION_STRING_USER = "1AZWarzgBu7T0qCqBvsZnNQmCPiU-8vdteMOcKuPBC14WtUC7pT3QuAG55Y6GtlbkZZ8XN_KDugD214Jqe-XExmoCW-FJdoO-c0PIDpEnLXYM61XRIpMh-WolwbhREweQY0FeGVuR2PfpnSEMOqlwb3wUC3lRxS6zGV-QzwxmiB_cpXVpDoSn61poZTcevExy_ao5cKVV5Zzjc9QF7uEhaRhCiDbENWUoZOQGqMDG5iT9PdbUf_Hd9tYElcb4jXjegsTDH-baufMF00Rxqp2_GQvGLk7Tq8DZqnugeB0hzZHrLNTqPrH5V0lJURcJS-yswbganim5kTTG5auZG9TnllbT6iM5Mv8="
ADMIN_ID = 7771137226
INDEX_FILE = "video_index_original.pkl"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BuddyMoviesBot:
    def __init__(self):
        self.bot = None; self.user = None
        self.idx = defaultdict(list); self.titles = {}
        self.ready = False; self.ecache = {}
        self.searches = {}
        if os.path.exists(INDEX_FILE):
            try:
                with open(INDEX_FILE, 'rb') as f:
                    data = pickle.load(f)
                self.titles = data.get('titles', {})
                self.idx = defaultdict(list, data.get('idx', {}))
                print(f"📂 Cargados {len(self.titles)} títulos")
                self.ready = True
            except: pass
        
    def _total(self): return len(self.titles)

    def _save_index(self):
        try:
            with open(INDEX_FILE, 'wb') as f:
                pickle.dump({'titles': self.titles, 'idx': dict(self.idx)}, f)
        except: pass

    async def _is_video(self, m):
        if not m or not m.media: return False
        try:
            if hasattr(m.media, 'document'):
                d = m.media.document
                if hasattr(d, 'mime_type') and d.mime_type and d.mime_type.startswith('video/'): return True
                for a in d.attributes:
                    if hasattr(a, 'video') and a.video: return True
            return hasattr(m.media, 'video')
        except: return False

    def _clean(self, t):
        if not t: return "Sin título"
        t = re.sub(r'https?://\S+', '', t); t = re.sub(r'@\w+', '', t)
        for l in t.split('\n'):
            c = l.strip()
            if 3 <= len(c.split()) <= 15 and len(c) > 10: return c
        return t.strip() or "Sin título"

    async def _search(self, q):
        if not self.ready: return []
        q_lower = q.lower().strip()
        r, s = [], set()
        for md in self.titles.values():
            if q_lower in md.get('clean_title', '').lower():
                uid = f"{md['entity_name']}_{md['message_id']}"
                if uid not in s: r.append(md); s.add(uid)
        return r[:20]

    def _create_buttons(self, results):
        btns = []
        for i, r in enumerate(results):
            btns.append([Button.inline(r['clean_title'][:50], f"send_{i}")])
        return btns

    async def _index(self, m, e):
        try:
            txt = m.text or m.caption or ''
            if not txt: return
            ct = self._clean(txt)
            words = re.findall(r'\b[a-zA-Z0-9]+\b', ct.lower())
            stop = {'de','la','el','y','en','con','para','por','un','una','hd','full','4k','1080p','720p','latino','español','subtitulado','the','and','with','for'}
            kw = [w for w in words if w not in stop and len(w) > 2]
            uname = self.ecache.get(e, {}).get('username', '')
            md = {'channel': e, 'clean_title': ct, 'message_id': m.id, 'entity_name': e, 'username': uname}
            for k in set(kw): self.idx[k].append(md)
            self.titles[hashlib.md5(ct.lower().encode()).hexdigest()[:12]] = md
        except: pass

    def _setup_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start(ev):
            await ev.reply(f"🎬 @BuddyMovies_Bot\n📊 {self._total()} videos\n🔍 Escribe lo que buscas")

        @self.bot.on(events.NewMessage(pattern='/addchannel'))
        async def addch(ev):
            if ev.sender_id != ADMIN_ID: return
            text = ev.text.replace('/addchannel', '').strip()
            channels = text.replace('\n', ' ').split()
            msg = await ev.reply(f"⏳ Indexando {len(channels)} canales...")
            total = 0
            for ch in channels:
                if not ch.startswith('@'): continue
                try:
                    ent = await self.user.get_entity(ch)
                    self.ecache[ch] = {'id': ent.id, 'username': getattr(ent, 'username', None)}
                    count = 0
                    async for m in self.user.iter_messages(ent, limit=None):
                        if await self._is_video(m):
                            await self._index(m, ch); count += 1
                            if count % 2000 == 0:
                                self._save_index()
                                try: await msg.edit(f"📊 {ch}: {count} títulos...")
                                except: pass
                    self.ready = True
                    total += count
                    self._save_index()
                    await ev.respond(f"✅ {ch}: {count} videos")
                except Exception as e:
                    await ev.respond(f"❌ {ch}: {e}")
            await msg.edit(f"✅ {total} títulos\n📊 Total: {self._total()}")

        @self.bot.on(events.NewMessage)
        async def handle(ev):
            if ev.out or not ev.text: return
            q = ev.text.strip()
            if len(q) < 2 or q.startswith('/'): return
            results = await self._search(q)
            if results:
                self.searches[ev.sender_id] = {'results': results}
                await ev.reply(f"🔍 {q}\n📊 {len(results)} resultados", buttons=self._create_buttons(results))
            else:
                await ev.reply("❌ Sin resultados")

        @self.bot.on(events.CallbackQuery(pattern=rb'^send_(\d+)$'))
        async def send_content(ev):
            idx = int(ev.data.decode().split('_')[1])
            results = self.searches.get(ev.sender_id, {}).get('results', [])
            if idx < len(results):
                r = results[idx]
                uname = r.get('username', '') or self.ecache.get(r['entity_name'], {}).get('username', '')
                if uname: link = f"https://t.me/{uname}/{r['message_id']}"
                else: link = f"https://t.me/c/{self.ecache.get(r['entity_name'], {}).get('id', '')}/{r['message_id']}"
                await ev.respond(f"🎬 ➠ {r['clean_title']}\n\n🔗 [ENLACE DIRECTO]({link})\n⚡ @BuddyMovies_Bot")
            await ev.answer("✅")

    async def start(self):
        self.user = TelegramClient(StringSession(SESSION_STRING_USER), API_ID, API_HASH)
        await self.user.start()
        self.bot = TelegramClient("bot_original", API_ID, API_HASH)
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
    except Exception as e: print(f"❌ Error: {e}")

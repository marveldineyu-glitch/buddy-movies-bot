import asyncio
import logging
import time
import threading
from telethon import TelegramClient, events, Button
import telebot
import re
import json
import os
from collections import defaultdict
import hashlib
import pickle

# 🔐 CREDENCIALES
API_ID = 28074212
API_HASH = "b18dae908474a377684922f3e9d5b795"
BOT_TOKEN = "8984212389:AAFZMh_ZQZm8DlIqPLvQEljnC1UPVtRJV-Q"

SESSION_STRING_USER = "1AZWarzQBu4JtB60pYeeTBFlwqbLPYLlRbCp4YsNhVrZR6jWk4ot18CG8GlGC4RtNtPdjbiRH1R38ojZD15V92q59-fr6PQaI8vfZF3iPKWQBVd_NYiHmXCi1haKN93WIilyNs__N79xtn6PfVFselPE_-iGqe3u7f4iierM_HtI13E-Y55DE71wPqqtbYRHC7zk2Hy2u87Kmpr8AOiozvGSUkjvKkWjuk0kiyOrN_heBNMzUTcTV9KQLxlJHelBmFq4MGt1oWpcii2cw6s9i8YDp3CYml_iyhQu_LpDHV38rsB352SaAstITawup8VbtaH4ZKvyAFcs0wYV3dc4GMN0Efybz618="

BOT_SESSION = "BuddyMoviesBot"
ADMIN_ID = 7771137226
ALLOWED_GROUP = "BuddyMovies_official"
RESULTS_PER_PAGE = 6
ID_VIDEO = "BAACAgEAAyEFAASVMPBpAANjaRo3eFQiNrmP1jRJBIIDXkHU5ZUAAi4BAAL7R0lHCKNISWgyguU2BA"
ID_FOTO_EXITO = "AgACAgEAAyEFAASVMPBpAANzaSKIAw5DdJgD91UkL69PW_-dMPgAAigMaxsYDxFFL7UwIAuTy64BAAMCAAN4AAM2BA"
ENLACE_GRUPO = "https://t.me/BuddyMovies_official"
META_INVITADOS = 1

TARGET_CHANNELS = ["@SeriesbyJoel", "@chatpeliculasymas", "@Almacen_Pelis", "@mundoword39", "@Neoanimes", "@AnimeLatinoHD", "@tiyiot"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from telethon.sessions import StringSession
except ImportError:
    class StringSession:
        def __init__(self, string): self.string = string
        def __str__(self): return self.string

# === BASE DE DATOS SIMPLE PARA RESULTADOS ===
import sqlite3
DB_FILE = "results.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS searches (user_id INTEGER, idx INTEGER, entity TEXT, title TEXT, msg_id INTEGER, username TEXT)")
    conn.commit()
    conn.close()

def save_search(user_id, results):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM searches WHERE user_id=?", (user_id,))
    for i, r in enumerate(results):
        entity_name = r.get('entity_name', '')
        title = r.get('clean_title', '')[:200]
        msg_id = r.get('message_id', 0)
        username = r.get('username', '')
        conn.execute("INSERT INTO searches VALUES (?,?,?,?,?,?)", (user_id, i, entity_name, title, msg_id, username))
    conn.commit()
    conn.close()

def get_search(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT * FROM searches WHERE user_id=? ORDER BY idx", (user_id,))
    results = [{'entity_name': r[2], 'clean_title': r[3], 'message_id': r[4], 'username': r[5]} for r in cur.fetchall()]
    conn.close()
    return results

init_db()

class UltraFastVideoBot:
    def __init__(self):
        self.bot_client = None
        self.user_client = None
        self.content_index = defaultdict(list)
        self.title_index = {}
        self.search_cache = {}
        self.is_index_ready = False
        self.scan_progress = {"completed": 0, "total": len(TARGET_CHANNELS)}
        self.accessible_entities = []
        self.entity_cache = {}
        self.channels_file = "canales_guardados.json"
        self.index_file = "video_index.pkl"
        self.scan_progress_file = "scan_progress.json"
        self.additional_channels = []
        
    async def initialize(self):
        try:
            print("🚀 INICIANDO BUDDY MOVIES BOT...")
            await self._load_saved_channels()
            await self._load_scan_progress()
            self.user_client = TelegramClient(session=StringSession(SESSION_STRING_USER), api_id=API_ID, api_hash=API_HASH)
            await self.user_client.start()
            self.bot_client = TelegramClient(BOT_SESSION, API_ID, API_HASH)
            await self.bot_client.start(bot_token=BOT_TOKEN)
            me = await self.user_client.get_me()
            print(f"✅ SESIÓN DE USUARIO: @{me.username}")
            await self._fast_entity_check()
            await self._load_existing_index()
            if not self.is_index_ready:
                print("⚡ ESCANEO RÁPIDO...")
                await self._quick_initial_scan()
            print("🔄 ESCANEO COMPLETO EN SEGUNDO PLANO...")
            asyncio.create_task(self._parallel_accelerated_scan())
            self._setup_handlers()
            print(f"\n🎯 BOT OPERATIVO - {self._get_total_videos()} VIDEOS")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    def _serialize_message_data(self, msg_data):
        return {'channel': msg_data['channel'], 'clean_title': msg_data['clean_title'], 'message_id': msg_data['message_id'], 'entity_name': msg_data['entity_name'], 'timestamp': msg_data.get('timestamp'), 'username': msg_data.get('username', '')}

    async def _load_existing_index(self):
        try:
            if os.path.exists(self.index_file):
                print("📂 CARGANDO ÍNDICE...")
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.content_index = defaultdict(list)
                    for key, messages in data.get('content_index', {}).items():
                        self.content_index[key] = messages
                    self.title_index = data.get('title_index', {})
                    self.entity_cache = data.get('entity_cache', {})
                print(f"✅ {self._get_total_videos()} videos cargados")
                self.is_index_ready = True
        except Exception as e:
            print(f"❌ Error: {e}")

    async def _save_index(self):
        try:
            serializable_content_index = {}
            for key, messages in self.content_index.items():
                serializable_content_index[key] = [self._serialize_message_data(msg) for msg in messages]
            serializable_title_index = {}
            for key, msg_data in self.title_index.items():
                serializable_title_index[key] = self._serialize_message_data(msg_data)
            data = {'content_index': serializable_content_index, 'title_index': serializable_title_index, 'entity_cache': self.entity_cache, 'saved_at': time.time()}
            with open(self.index_file, 'wb') as f:
                pickle.dump(data, f)
        except: pass

    async def _load_scan_progress(self):
        try:
            if os.path.exists(self.scan_progress_file):
                with open(self.scan_progress_file, 'r') as f:
                    self.scan_progress = json.load(f)
        except: pass

    async def _fast_entity_check(self):
        for entity_name in TARGET_CHANNELS + self.additional_channels:
            try:
                entity = await self.user_client.get_entity(entity_name)
                self.accessible_entities.append(entity_name)
                self.entity_cache[entity_name] = {'id': entity.id, 'username': getattr(entity, 'username', None), 'access_hash': entity.access_hash}
            except: pass

    async def _quick_initial_scan(self):
        for entity_name in self.accessible_entities[:3]:
            try:
                async for message in self.user_client.iter_messages(entity_name, limit=500):
                    if await self._is_video_message(message):
                        await self._index_message(message, entity_name)
            except: pass
        self.is_index_ready = True
        await self._save_index()

    async def _parallel_accelerated_scan(self):
        for entity_name in self.accessible_entities:
            await self._complete_channel_scan(entity_name)

    async def _complete_channel_scan(self, entity_name):
        try:
            async for message in self.user_client.iter_messages(entity_name, limit=2000):
                if await self._is_video_message(message):
                    await self._index_message(message, entity_name)
            self.scan_progress["completed"] += 1
            await self._save_index()
        except: pass

    async def _is_video_message(self, message):
        if not message or not message.media: return False
        try:
            if hasattr(message.media, 'document'):
                doc = message.media.document
                if hasattr(doc, 'mime_type') and doc.mime_type:
                    return doc.mime_type.startswith('video/')
                for attr in doc.attributes:
                    if hasattr(attr, 'video') and attr.video: return True
            return hasattr(message.media, 'video')
        except: return False

    def _clean_content_title(self, text):
        if not text: return "Contenido sin título"
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        for line in text.split('\n'):
            clean = line.strip()
            if 3 <= len(clean.split()) <= 15 and len(clean) > 10: return clean
        return text.strip() if text.strip() else "Contenido sin título"

    async def _index_message(self, message, entity_name):
        try:
            text = ""
            if hasattr(message, 'text') and message.text: text = message.text
            elif hasattr(message, 'caption') and message.caption: text = message.caption
            if not text: return
            clean_title = self._clean_content_title(text)
            words = re.findall(r'\b[a-zA-Z0-9]+\b', clean_title.lower())
            stop_words = {'de','la','el','y','en','con','para','por','un','una','hd','full','4k','1080p','720p','latino','español','subtitulado','the','and','with','for','www','com'}
            keywords = [w for w in words if w not in stop_words and len(w) > 2]
            username = self.entity_cache.get(entity_name, {}).get('username', '')
            msg_data = {'channel': entity_name, 'clean_title': clean_title, 'message_id': message.id, 'entity_name': entity_name, 'timestamp': time.time(), 'username': username}
            for keyword in set(keywords):
                self.content_index[keyword].append(msg_data)
            title_hash = hashlib.md5(clean_title.lower().encode()).hexdigest()[:12]
            self.title_index[title_hash] = msg_data
        except: pass

    def _get_total_videos(self):
        unique_videos = set()
        for messages in self.content_index.values():
            for msg in messages:
                unique_videos.add(f"{msg['entity_name']}_{msg['message_id']}")
        return len(unique_videos)

    async def _is_allowed_chat(self, event):
        if event.sender_id == ADMIN_ID: return True
        try:
            chat = await event.get_chat()
            if hasattr(chat, 'username') and chat.username == ALLOWED_GROUP.replace('@', ''): return True
        except: pass
        return False

    async def _send_private_message(self, event):
        try:
            user = await event.get_sender()
            await event.reply(f"👋 ¡Hola {user.first_name}!\n\nÚnete al grupo: {ENLACE_GRUPO}", link_preview=False)
        except: pass

    async def _load_saved_channels(self):
        try:
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    self.additional_channels = json.load(f).get('additional_channels', [])
        except: pass

    async def _precise_search(self, query):
        if not self.is_index_ready: return []
        query_lower = query.lower().strip()
        query_words = [w for w in re.findall(r'\b\w+\b', query_lower) if len(w) > 2]
        if not query_words: return []
        results = []
        seen = set()
        for word in query_words:
            if word in self.content_index:
                for msg in self.content_index[word]:
                    uid = f"{msg['entity_name']}_{msg['message_id']}"
                    if uid not in seen:
                        results.append(msg)
                        seen.add(uid)
        return results

    def _setup_handlers(self):
        @self.bot_client.on(events.NewMessage(pattern='/start'))
        async def start(event):
            if not await self._is_allowed_chat(event):
                await self._send_private_message(event)
                return
            await event.reply(f"🎬 **BUDDY MOVIES BOT** ⚡\n\n📊 **{self._get_total_videos()} videos**\n🔍 Escribe lo que buscas")

        @self.bot_client.on(events.NewMessage)
        async def search(event):
            try:
                if event.out or (event.text and event.text.startswith('/')): return
                if not await self._is_allowed_chat(event):
                    await self._send_private_message(event)
                    return
                query = event.text.strip()
                if len(query) < 2: return
                results = await self._precise_search(query)
                if results:
                    save_search(event.sender_id, results)
                    buttons = []
                    for i, r in enumerate(results[:RESULTS_PER_PAGE]):
                        title = r['clean_title'][:50]
                        buttons.append([Button.inline(title, f"send_{i}")])
                    await event.reply(f"🔍 **{query}**\n📊 {len(results)} resultados\n👇 Selecciona:", buttons=buttons)
                else:
                    await event.reply(f"❌ Sin resultados para: `{query}`")
            except Exception as e:
                print(f"Error search: {e}")

        @self.bot_client.on(events.CallbackQuery(pattern=rb'^send_(\d+)$'))
        async def send_content(event):
            try:
                idx = int(event.data.decode().split('_')[1])
                results = get_search(event.sender_id)
                if idx < len(results):
                    r = results[idx]
                    entity_name = r['entity_name']
                    title = r['clean_title']
                    msg_id = r['message_id']
                    username = r.get('username', '')
                    
                    entity_cache = self.entity_cache.get(entity_name, {})
                    if not username and entity_cache:
                        username = entity_cache.get('username', '')
                    
                    if username:
                        link = f"https://t.me/{username}/{msg_id}"
                    else:
                        entity_id = entity_cache.get('id', entity_name)
                        link = f"https://t.me/c/{entity_id}/{msg_id}"
                    
                    caption = f"🎬 ➠ {title}\n\n🔗 [ENLACE DIRECTO]({link})\n⚡ @BuddyMoviesBot"
                    await event.respond(caption, link_preview=True)
                await event.answer("✅ Enviado!")
            except Exception as e:
                print(f"Error send: {e}")
                await event.answer("❌ Error")

    async def run(self):
        try:
            await self.bot_client.run_until_disconnected()
        except:
            await asyncio.sleep(10)
            await self.run()

class InvitationBot:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.usuarios_pendientes = {}
        self.usuarios_file = "usuarios_invitacion.json"
        self._load_usuarios()
        
    def _load_usuarios(self):
        try:
            if os.path.exists(self.usuarios_file):
                with open(self.usuarios_file, 'r') as f:
                    self.usuarios_pendientes = json.load(f)
        except: pass

    def setup_handlers(self):
        @self.bot.message_handler(content_types=['new_chat_members'])
        def entrada(message):
            try:
                self.bot.delete_message(message.chat.id, message.message_id)
            except: pass

        @self.bot.message_handler(func=lambda m: True)
        def filtro(message):
            try:
                if message.from_user.id in self.usuarios_pendientes:
                    self.bot.delete_message(message.chat.id, message.message_id)
                    self.bot.restrict_chat_member(message.chat.id, message.from_user.id, permissions=telebot.types.ChatPermissions(can_send_messages=False, can_invite_users=True))
            except: pass

    def run(self):
        self.setup_handlers()
        while True:
            try:
                self.bot.infinity_polling(timeout=60)
            except:
                time.sleep(10)

async def main():
    bot = UltraFastVideoBot()
    inv = InvitationBot()
    threading.Thread(target=inv.run, daemon=True).start()
    await bot.initialize()
    await bot.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Bot detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(30)
        asyncio.run(main())

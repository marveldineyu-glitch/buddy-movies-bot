const TOKEN = '8656794267:AAEgO7R-3KTphpb6CNkaW90VTbEtsdNq7dw';
const DB_ID = 'ec8f8e4a-9f92-4cdc-b6cd-0ca648019870';
const ACCOUNT = 'b228e7b982da76605a0b65ad30798ccb';
const API_TOKEN = 'cfut_3xFydCDV69GDs4j4B3lRL48Ajp5JjmFsgAodiO8t21536139';
const TG = `https://api.telegram.org/bot${TOKEN}`;
const GRUPO_ID = -1002311102965;
const GRUPO_LINK = 'https://t.me/BuddyMovies_official';
const RES_PER_PAGE = 10;
const MAX_RESULTS = 5000;

const CACHE = new Map();
const RATE_LIMIT = new Map();
const CACHE_TTL = 30 * 60 * 1000;

function cleanupCache() {
  const now = Date.now();
  for (const [key, value] of CACHE) {
    if (now - value.timestamp > CACHE_TTL) CACHE.delete(key);
  }
  for (const [key, value] of RATE_LIMIT) {
    if (now > value.resetTime) RATE_LIMIT.delete(key);
  }
}

function rateLimit(userId) {
  const now = Date.now();
  const userLimit = RATE_LIMIT.get(userId);
  if (userLimit && now < userLimit.resetTime) {
    if (userLimit.count >= 30) return false;
    userLimit.count++;
  } else {
    RATE_LIMIT.set(userId, { count: 1, resetTime: now + 60000 });
  }
  return true;
}

async function buscarEnD1(query) {
  const safeQuery = query.replace(/'/g, "''").replace(/\\/g, '\\\\');
  const sql = `SELECT titulo, enlace FROM peliculas WHERE titulo LIKE '%${safeQuery}%' LIMIT ${MAX_RESULTS}`;
  const url = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT}/d1/database/${DB_ID}/query`;
  
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${API_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql })
  });
  
  const data = await res.json();
  const results = data?.result?.[0]?.results || [];
  
  return {
    resultados: results,
    total: results.length,
    hayMas: results.length >= MAX_RESULTS
  };
}

async function sendMessage(chat_id, text, reply_markup = null, reply_to = null) {
  const body = { chat_id, text, parse_mode: 'HTML', disable_web_page_preview: false };
  if (reply_markup) body.reply_markup = JSON.stringify(reply_markup);
  if (reply_to) body.reply_to_message_id = reply_to;
  
  const res = await fetch(`${TG}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return res.json();
}

async function editMessageText(chat_id, msg_id, text, reply_markup = null) {
  const body = { chat_id, message_id: msg_id, text, parse_mode: 'HTML', disable_web_page_preview: false };
  if (reply_markup) body.reply_markup = JSON.stringify(reply_markup);
  
  return fetch(`${TG}/editMessageText`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
}

async function answerCallback(callback_id, text, show_alert = false) {
  return fetch(`${TG}/answerCallbackQuery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ callback_query_id: callback_id, text, show_alert, cache_time: 0 })
  });
}

function buildKeyboard(resultados, page, total, hayMas) {
  const totalPages = Math.ceil(total / RES_PER_PAGE);
  const start = page * RES_PER_PAGE;
  const batch = resultados.slice(start, start + RES_PER_PAGE);
  
  const keyboard = { inline_keyboard: [] };
  
  batch.forEach((r, i) => {
    const idx = start + i;
    const tituloCorto = r.titulo.length > 45 ? r.titulo.substring(0, 42) + '...' : r.titulo;
    keyboard.inline_keyboard.push([{
      text: `🎬 ${tituloCorto}`,
      callback_data: `get_${idx}_${page}`
    }]);
  });
  
  if (totalPages > 1) {
    const nav = [];
    if (page > 0) nav.push({ text: '⬅️', callback_data: `p_${page-1}` });
    
    let pageInfo = `📄 ${page+1}/${totalPages}`;
    if (hayMas && page === totalPages - 1) pageInfo += '+';
    nav.push({ text: pageInfo, callback_data: 'noop' });
    
    if (page < totalPages - 1) nav.push({ text: '➡️', callback_data: `p_${page+1}` });
    keyboard.inline_keyboard.push(nav);
  }
  
  keyboard.inline_keyboard.push([{ text: '🔍 Nueva búsqueda', callback_data: 'newsearch' }]);
  
  return keyboard;
}

async function handleCallback(cb) {
  const data = cb.data;
  const msg = cb.message;
  const chat_id = msg.chat.id;
  const msg_id = msg.message_id;
  const user_id = cb.from.id;
  const user_name = cb.from.first_name || 'Usuario';
  
  const cbPromise = answerCallback(cb.id, '⏳ Cargando...');
  
  if (data === 'noop') {
    await cbPromise;
    return;
  }
  
  if (data === 'newsearch') {
    await answerCallback(cb.id, '✏️ Escribe un nuevo título', true);
    return;
  }
  
  if (data.startsWith('p_')) {
    const page = parseInt(data.split('_')[1]);
    const cached = CACHE.get(`${msg_id}`);
    
    if (cached) {
      const totalPages = Math.ceil(cached.total / RES_PER_PAGE);
      const keyboard = buildKeyboard(cached.resultados, page, cached.total, cached.hayMas);
      const masTexto = cached.hayMas ? '\n⚠️ <i>Mostrando máx. 5000 resultados</i>' : '';
      const texto = `👋 <b>${user_name}</b>\n\n` +
                    `🔍 <b>${cached.query}</b>\n` +
                    `📊 <b>${cached.total.toLocaleString()} resultados</b> · Página ${page+1}/${totalPages}${masTexto}\n\n` +
                    `🔻 <i>Selecciona para obtener el enlace</i>`;
      
      await Promise.all([
        cbPromise,
        editMessageText(chat_id, msg_id, texto, keyboard)
      ]);
      
      await answerCallback(cb.id, `📄 Página ${page+1}/${totalPages}`);
    } else {
      await answerCallback(cb.id, '⚠️ Búsqueda expirada. Escribe de nuevo.', true);
    }
    return;
  }
  
  if (data.startsWith('get_')) {
    const parts = data.split('_');
    const idx = parseInt(parts[1]);
    const cached = CACHE.get(`${msg_id}`);
    
    if (cached && cached.resultados[idx]) {
      const r = cached.resultados[idx];
      
      await Promise.all([
        cbPromise,
        sendMessage(chat_id, `🎬 <b>${r.titulo}</b>\n\n📥 <a href="${r.enlace}">🔗 ENLACE DIRECTO</a>\n\n⚡ <i>@BuddyPelis_Bot</i>`, null, msg_id),
        answerCallback(cb.id, '✅ Enlace enviado')
      ]);
    } else {
      await answerCallback(cb.id, '⚠️ Sesión expirada. Busca de nuevo.', true);
    }
    return;
  }
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  if (request.method !== 'POST') return new Response('OK');
  
  cleanupCache();
  
  try {
    const body = await request.json();
    
    if (body.callback_query) {
      await handleCallback(body.callback_query);
      return new Response('OK');
    }
    
    const msg = body.message;
    if (!msg?.text) return new Response('OK');
    
    const chat_id = msg.chat.id;
    const user_id = msg.from.id;
    const user_name = msg.from.first_name || 'Usuario';
    const query = msg.text.trim();
    const msg_id = msg.message_id;
    
    if (query === '/start' || query === '/start@BuddyPelis_Bot') {
      if (msg.chat.type === 'private') {
        await sendMessage(chat_id, 
          `🎬 <b>¡BuddyPelis!</b>\n\n` +
          `📽️ <b>+150,000 películas y series</b>\n` +
          `🔍 Busca sin límites en el grupo\n\n` +
          `👉 <b>Únete:</b> ${GRUPO_LINK}`,
          { inline_keyboard: [[{ text: '🎥 IR AL GRUPO', url: GRUPO_LINK }]] }
        );
      } else {
        await sendMessage(chat_id, 
          `🎬 <b>BuddyPelis Bot</b>\n\n` +
          `✏️ Escribe el nombre de una película o serie\n` +
          `🔍 Ejemplo: <code>Barbie</code> · <code>Avengers</code>\n` +
          `📊 <b>+150k videos disponibles</b>`
        );
      }
      return new Response('OK');
    }
    
    if (chat_id !== GRUPO_ID) {
      await sendMessage(chat_id, `🔒 Este bot solo funciona en:\n👉 ${GRUPO_LINK}`);
      return new Response('OK');
    }
    
    if (!rateLimit(user_id)) {
      await sendMessage(chat_id, `⏳ <b>Espera un momento</b>\nDemasiadas búsquedas. Intenta en 1 minuto.`, null, msg_id);
      return new Response('OK');
    }
    
    const { resultados, total, hayMas } = await buscarEnD1(query);
    
    if (resultados.length === 0) {
      await sendMessage(chat_id, 
        `<b>🔍 ${query}</b>\n\n` +
        `<b>❌ No se encontraron resultados.</b>\n` +
        `<b>🎬 ¿Probaste con:</b>\n` +
        `<b>•</b> El título exacto\n` +
        `<b>•</b> Sin abreviaturas\n` +
        `<b>•</b> Solamente el nombre principal?\n\n` +
        `<b>💡 Un pequeño cambio puede hacer la diferencia.</b>\n` +
        `<b>🔄 ¡Seguí buscando!</b>`,
        null, msg_id
      );
    } else {
      const totalPages = Math.ceil(total / RES_PER_PAGE);
      const masTexto = hayMas ? '\n⚠️ <i>Mostrando máx. 5000 resultados</i>' : '';
      const texto = `👋 <b>${user_name}</b>\n\n` +
                    `🔍 <b>${query}</b>\n` +
                    `📊 <b>${total.toLocaleString()} resultados</b> · Página 1/${totalPages}${masTexto}\n\n` +
                    `🔻 <i>Selecciona un título para obtener el enlace</i>`;
      
      const keyboard = buildKeyboard(resultados, 0, total, hayMas);
      const sent = await sendMessage(chat_id, texto, { inline_keyboard: keyboard.inline_keyboard }, msg_id);
      
      if (sent.ok) {
        CACHE.set(`${sent.result.message_id}`, {
          resultados,
          total,
          query,
          user_id,
          hayMas,
          timestamp: Date.now()
        });
      }
    }
    
    return new Response('OK');
    
  } catch (error) {
    console.error('Error:', error);
    return new Response('OK');
  }
}

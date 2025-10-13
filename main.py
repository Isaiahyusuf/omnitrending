# main.py - OmniTrending (merged features)
#import asyncio
#from aiogram import Bot, Dispatcher, types
#from aiogram.utils import executor
#from keep_alive import keep_alive  # ✅ place here
import os
import aiohttp
import asyncio
import logging
import sqlite3
from io import BytesIO
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import json
import math
import traceback
#from keep_alive import keep_alive  # make sure this line is near your imports at the top
# ---------------- Load Bot Token ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT")  # Optional support chat id (string or int)

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not found!")

# ---------------- Admin / Channel config ----------------
SUPPORT_IDS = [8435563121]                   # Allowed support user IDs (will receive debug messages)
CHANNEL_ID =-1002271758972





# ---------------- Footer / Branding ----------------
POST_FOOTER = "\n\n🌐 OmniTrending • visibility for your TOKEN\n⚠️ This is informational only — not financial advice. Always DYOR."

# ---------------- Logging setup (console + file) ----------------
logger = logging.getLogger("omnitrending")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# Optional rotating file log (uncomment if you want file logs)
try:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler("omnitrending.log", maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)
except Exception:
    pass

# ---------------- Payment Wallets ----------------
PAYMENT_WALLETS = {
    "solana": "BUBMVmvrUVGmN29jFiKEJopjdKFPifSew3cDT1CB5Xah",
    "ethereum": "0xbc0F786476d68dfC99FCd20D58F887b97fEa7204",
    "base": "0xbc0F786476d68dfC99FCd20D58F887b97fEa7204",
    "bsc": "0xdbf228F9B48dccf2099CA0f824073D9B69a23914",
    "arbitrum": "0xdbf228F9B48dccf2099CA0f824073D9B69a23914"
}

# ---------------- Trending Packages ----------------
TRENDING_PACKAGES = {
    "solana": {"3h": 1.2, "12h": 4.5, "24h": 9},
    "ethereum": {"3h": 0.0593, "12h": 0.2223, "24h": 0.4447},
    "base": {"3h": 0.0593, "12h": 0.2223, "24h": 0.4447},
    "bsc": {"3h": 0.2066, "12h": 0.7745, "24h": 1.5489},
    "arbitrum": {"3h": 0.0593, "12h": 0.2223, "24h": 0.4447}
}

# ---------------- Chain ID mapping ----------------
CHAIN_IDS = {
    "solana": "solana",
    "ethereum": "ethereum",
    "bsc": "bsc",
    "base": "base",
    "arbitrum": "arbitrum"
}

# ---------------- Network Emojis ----------------
NETWORK_EMOJIS = {
    "solana": "💜",
    "ethereum": "💠",
    "bsc": "🟡",
    "base": "🧊",
    "arbitrum": "⚪"
}

# ---------------- Initialize Bot ----------------
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

# ---------------- States ----------------
class UserState(StatesGroup):
    waiting_for_ca = State()
    waiting_for_trend_package = State()
    waiting_for_payment = State()
    trending_active = State()

# ---------------- Runtime session storage ----------------
# key = session_id (channel message id), value = dict with session details
TREND_SESSIONS = {}
# store user contracts temporarily (for activate by support path)
user_contracts = {}

# thresholds to watch (percent)
THRESHOLDS = [10, 20, 30, 40, 50, 60, 70]

# poll interval in seconds for checking updates (light polling).
# We will still send a debug to support every poll as requested.
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

# ---------------- Simple SQLite persistence (watchlist + alerts) ----------------
DB_FILE = os.getenv("DATABASE_FILE", "omnitrending.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain TEXT,
            pair TEXT,
            note TEXT,
            added_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alert_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT,
            pair TEXT,
            details TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_watchlist(chain, pair, note=""):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO watchlist (chain, pair, note, added_at) VALUES (?, ?, ?, ?)",
                (chain, pair, note, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def remove_watchlist(pair):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist WHERE pair = ?", (pair,))
    conn.commit()
    conn.close()

def list_watchlist():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT chain, pair, note, added_at FROM watchlist ORDER BY added_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def log_alert(event, pair, details):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO alert_log (event, pair, details, created_at) VALUES (?, ?, ?, ?)",
                (event, pair, json.dumps(details, default=str), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# initialize DB at startup
init_db()

# ---------------- Helpers ----------------
# ---------------- Helpers ----------------

    # DexScreener returns an array; take first result
chain_id = pairs[0].get("chainId", "").lower()
return chain_id or None



    # EVM chains: Ethereum, BSC, Base, Arbitrum
if network in ["ethereum", "bsc", "base", "arbitrum"]:
        return Web3.is_address(ca)

    # Solana uses Base58 and is validated differently
elif network == "solana":
try:
    PublicKey(ca)
            return True
except
Exception:
            return False
    return False


async def send_support_log(level: str, text: str, extra: dict = None):
    """Send a short log message to all SUPPORT_IDS and print log to console/file."""
    ...

async def send_support_log(level: str, text: str, extra: dict = None):
    """Send a short log message to all SUPPORT_IDS and print log to console/file."""
    timestamp = datetime.utcnow().isoformat()
    body = f"[{level}] {timestamp}\n{text}"
    if extra:
        try:
            body += "\n\n" + json.dumps(extra, default=str)[:1900]
        except:
            pass

    # Send to support IDs (DM)
    for sid in SUPPORT_IDS:
        try:
            await bot.send_message(sid, body, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not send support log to {sid}: {e}")

    # Also log locally
    if level.upper() == "ERROR":
        logger.error(text)
    elif level.upper() == "WARN" or level.upper() == "WARNING":
        logger.warning(text)
    else:
        logger.info(text)

# ---------------- Analytics / Safety functions (new) ----------------
def compute_safety_score(pair_data: dict):
    """
    Heuristic score: higher = more notable / suspicious.
    Not a buy/sell recommendation.
    """
    score = 0
    try:
        liquidity = pair_data.get('liquidity', {}).get('usd') or pair_data.get('liquidityUsd') or 0
        if liquidity is None:
            liquidity = 0
        try:
            liquidity = float(liquidity)
        except:
            liquidity = 0

        # price movement
        h1 = 0
        try:
            h1 = float(pair_data.get('priceChange', {}).get('h1', 0) or 0)
        except:
            try:
                h1 = float(pair_data.get('priceChange1h', 0) or 0)
            except:
                h1 = 0

        age_seconds = int(pair_data.get('ageSeconds') or pair_data.get('age') or 0)

        # heuristics
        if liquidity < 1000:
            score += 3
        elif liquidity < 10000:
            score += 1

        if abs(h1) >= 10:
            score += 2
        if age_seconds and age_seconds < 3600:
            score += 2

        owner_pct = float(pair_data.get('ownerHoldingsPercent') or pair_data.get('owner_percent') or 0)
        if owner_pct > 50:
            score += 3

    except Exception:
        logger.debug("Error computing safety score", exc_info=True)
    return int(score)

def quick_honeypot_check(pair_data: dict):
    flags = []
    try:
        age_seconds = int(pair_data.get('ageSeconds') or pair_data.get('age') or 0)
        liquidity = pair_data.get('liquidity', {}).get('usd') or pair_data.get('liquidityUsd') or 0
        if liquidity is None:
            liquidity = 0
        owner_pct = float(pair_data.get('ownerHoldingsPercent') or pair_data.get('owner_percent') or 0)
        if age_seconds and age_seconds < 3600:
            flags.append("very_new")
        if liquidity and float(liquidity) < 1000:
            flags.append("low_liquidity")
        if owner_pct and owner_pct > 50:
            flags.append("high_owner_concentration")
        if not pair_data.get('info',{}).get('imageUrl') and not pair_data.get('baseToken',{}).get('imageUrl'):
            flags.append("no_logo")
        if not pair_data.get('explorer') and not pair_data.get('baseToken',{}).get('explorer'):
            flags.append("no_explorer")
    except Exception:
        logger.debug("Error in honeypot check", exc_info=True)
    return {"flags": flags, "flag_count": len(flags)}

# ---------------- Utils (fetch/format/resize) ----------------
async def fetch_from_pumpportal(token_address: str):
    """
    Try to fetch pump.fun / pumpportal style data.
    This is an attempt; many providers exist (PumpPortal, QuickNode add-ons, Bitquery, Moralis).
    We attempt a few likely endpoints if reachable, otherwise return None.
    """
    try:
        # try pumpportal.fun public path
        urls = [
            f"https://pumpportal.fun/api/token/{token_address}",
            f"https://pumpportal.fun/api/v1/token/{token_address}",
            f"https://api.pumpportal.fun/token/{token_address}"
        ]
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for url in urls:
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            # normalize to our expected shape if possible
                            if data:
                                return data
                except Exception:
                    continue
    except Exception:
        pass
    return None

DEXSCREENER_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/"


DEXSCREENER_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/"

async def fetch_from_dexscreener(token_address: str):
    """Fetch token info from Dexscreener tokens endpoint.
    Returns the parsed JSON dict or None on failure.
    """
    url = DEXSCREENER_TOKEN_URL + token_address
    headers = {"User-Agent": "OmniTrending/1.0 (+https://example.com)"}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    print(f"[Dexscreener] tokens API HTTP {resp.status} for {token_address}")
                    return None
                data = await resp.json()
                if not data or "pairs" not in data or not data["pairs"]:
                    print(f"[Dexscreener] tokens API returned no pairs for {token_address}")
                    return None
                return data
    except Exception as e:
        print(f"[Dexscreener] fetch error for {token_address}: {e}")
        return None


PUMP_API = "https://pump.fun/api/v1/token/"

async def fetch_from_pumpfun(token_address: str):
    """Try pump.fun API as a fallback. Returns parsed JSON or None."""
    url = PUMP_API + token_address
    headers = {"User-Agent": "OmniTrending/1.0 (+https://example.com)"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return data
                else:
                    print(f"[Pump.fun] HTTP {resp.status} for {token_address}")
                    return None
    except Exception as e:
        print(f"[Pump.fun] fetch error for {token_address}: {e}")
        return None

async def fetch_token_info_auto(chain_id: str, token_address: str):
    """
    Try pumpportal/pump.fun style APIs first (for Solana), then Dexscreener fallback.
    Returns normalized pair-like object expected by the rest of the code (best-effort).
    """
    # try pump portal / pump.fun providers only for Solana
    if chain_id.lower() == "solana":
        try:
            pump_data = await fetch_from_pumpportal(token_address)
            if pump_data:
                # some pump APIs return 'pairs' or token info; try to adapt
                # If pump_data contains 'pair' or 'price' keys, return as-is
                return pump_data
        except Exception:
            pass

    # fallback to Dexscreener
    ds = await fetch_from_dexscreener(token_address)
    if ds and 'pairs' in ds and ds['pairs']:
        # choose best chain match if possible
        # If the token returned a pair object, return the chosen pair
        # fallback: return first pair
        try:
            chain_lower = chain_id.lower()
            pairs = ds.get('pairs', [])
            if isinstance(pairs, list) and len(pairs) > 0:
                # prefer pair whose chainId or chain matches
                for p in pairs:
                    if p.get('chainId','').lower() == chain_lower or p.get('chain','').lower() == chain_lower:
                        return p
                return pairs[0]
        except Exception:
            return ds
    return ds

def format_number(num):
    try:
        num = float(num)
        if num >= 1_000_000_000:
            return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"${num/1_000:.2f}K"
        else:
            return f"${num:.2f}"
    except:
        return "N/A"

def format_percentage(num):
    try:
        num = float(num)
        if num > 0: return f"🟢 +{num:.2f}%"
        elif num < 0: return f"🔴 {num:.2f}%"
        else: return f"⚪ {num:.2f}%"
    except:
        return "⚪ N/A"

async def resize_image(url, size=(300,300)):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                img_bytes = await resp.read()
                img = Image.open(BytesIO(img_bytes))

                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background

                # Create square canvas with padding
                max_dim = max(img.size)
                square_img = Image.new('RGB', (max_dim, max_dim), (255, 255, 255))
                offset = ((max_dim - img.size[0]) // 2, (max_dim - img.size[1]) // 2)
                square_img.paste(img, offset)

                # Resize to target size
                square_img.thumbnail(size, Image.Resampling.LANCZOS)

                bio = BytesIO()
                bio.name = "logo.png"
                square_img.save(bio, format="PNG", quality=95)
                bio.seek(0)
                return bio
    except Exception as e:
        await send_support_log("ERROR", f"Error resizing image: {e}", {"url": url})
        return None

# ---------------- "AI" summary generator (local heuristics) ----------------
def ai_style_summary(pair_data, pct_change=None):
    """Return a short human-friendly summary based on metrics (no external AI)."""
    try:
        name = pair_data.get('baseToken',{}).get('name') or pair_data.get('name') or pair_data.get('tokenName') or "Token"
        symbol = pair_data.get('baseToken',{}).get('symbol') or pair_data.get('symbol') or "TOKEN"
        liquidity = pair_data.get('liquidity',{}).get('usd') or pair_data.get('liquidityUsd') or 0
        vol = pair_data.get('volume',{}).get('h24') or pair_data.get('volume24h') or 0
        flags = quick_honeypot_check(pair_data).get('flags', [])
        score = compute_safety_score(pair_data)
        parts = []
        parts.append(f"{symbol} ({name}) — safety score {score}/10.")
        parts.append(f"Liquidity: {format_number(liquidity)} • 24h vol: {format_number(vol)}.")
        if pct_change is not None:
            parts.append(f"Change vs baseline: {pct_change:.2f}%")
        if flags:
            parts.append("Flags: " + ", ".join(flags))
        parts.append("This is informational only — not financial advice. Always DYOR.")
        return " ".join(parts)
    except Exception as e:
        return "Summary unavailable."

# ---------------- Create professional message (kept mostly same) ----------------
def create_professional_message(pair_data, chain_name):
    if not pair_data:
        return None, None, None
    base_token = pair_data.get('baseToken',{})
    price_usd = pair_data.get('priceUsd','N/A')
    price_change_h24 = pair_data.get('priceChange',{}).get('h24',0)
    price_change_h6 = pair_data.get('priceChange',{}).get('h6',0)
    price_change_h1 = pair_data.get('priceChange',{}).get('h1',0)
    volume_24h = pair_data.get('volume',{}).get('h24',0) or pair_data.get('volume24h',0)
    liquidity = pair_data.get('liquidity',{}).get('usd',0)
    fdv = pair_data.get('fdv',0)
    market_cap = pair_data.get('marketCap',0)
    pair_chain = pair_data.get('chainId','Unknown')
    dex_name = pair_data.get('dexId','Unknown')
    pair_address = pair_data.get('pairAddress','') or pair_data.get('address','') or pair_data.get('pair','')
    logo_url = pair_data.get('info',{}).get('imageUrl') or base_token.get('imageUrl') or pair_data.get('image')

    # Price formatting
    try:
        price_float = float(price_usd)
        if price_float < 0.000001: price_display = f"${price_float:.10f}"
        elif price_float < 0.01: price_display = f"${price_float:.8f}"
        else: price_display = f"${price_float:.6f}"
    except: price_display = "N/A"

    network_emoji = NETWORK_EMOJIS.get(pair_chain.lower(),"🔗")

    message = (
        f"╔══════════════════════════╗\n"
        f"     <b>🎯 TOKEN ANALYTICS</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{network_emoji} <b>{base_token.get('symbol','Unknown')}</b> • {base_token.get('name','Unknown')}\n"
        f"🏦 <b>DEX:</b> {dex_name.upper()}\n"
        f"⛓️ <b>Chain:</b> {pair_chain.upper()}\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  <b>💰 PRICE INFORMATION</b>   ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
        f"💵 <b>Current Price:</b> {price_display}\n\n"
        f"📊 <b>Price Changes:</b>\n"
        f"  • 1H:  {format_percentage(price_change_h1)}\n"
        f"  • 6H:  {format_percentage(price_change_h6)}\n"
        f"  • 24H: {format_percentage(price_change_h24)}\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  <b>📈 MARKET STATISTICS</b>   ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
        f"💎 <b>Market Cap:</b> {format_number(market_cap)}\n"
        f"🌊 <b>Liquidity:</b> {format_number(liquidity)}\n"
        f"📊 <b>24h Volume:</b> {format_number(volume_24h)}\n"
        f"💹 <b>FDV:</b> {format_number(fdv)}\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  <b>📝 CONTRACT INFO</b>       ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
        f"<code>{base_token.get('address','N/A') or pair_address}</code>\n"
    )
    chart_url = f"https://dexscreener.com/{pair_chain}/{pair_address}" if pair_address else None
    return logo_url, message, chart_url

# ---------------- Start Command ----------------
@dp.message_handler(commands=['start'], state='*')
async def start_command(message: types.Message, state: FSMContext):
    await state.finish()
    user_first = message.from_user.first_name or "there"
    start_text = (
        f"╔══════════════════════════╗\n"
        f"  <b>🌟 OMNITRENDING BOT 🌟</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"👋 Welcome, <b>{user_first}</b>!\n\n"
        f"Your professional multi-chain DEX analytics platform.\n\n"
        f"<b>📊 Track & Trend Across:</b>\n"
        f"💜 Solana  |  💠 Ethereum  |  🟡 BSC\n"
        f"🧊 Base  |  ⚪ Arbitrum\n\n"
        f"Select a network below to get started! 👇"
    )
    buttons = [
        [InlineKeyboardButton("💜 Solana", callback_data="select_solana")],
        [InlineKeyboardButton("💠 Ethereum", callback_data="select_ethereum")],
        [InlineKeyboardButton("🟡 BSC", callback_data="select_bsc")],
        [InlineKeyboardButton("🧊 Base", callback_data="select_base")],
        [InlineKeyboardButton("⚪ Arbitrum", callback_data="select_arbitrum")],
        [InlineKeyboardButton("💰 Prices", callback_data="show_prices")],
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(start_text, reply_markup=keyboard)

# ---------------- Network Selection ----------------
# ------------------ detect actual network via DexScreener ------------------


# ---------------------------------------------------------------------------

@dp.callback_query_handler(lambda c: c.data.startswith("select_"), state='*')
async def handle_network_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    network = callback_query.data.split("_")[1]
    await state.update_data(selected_network=network)
    await UserState.waiting_for_ca.set()
    network_emoji = NETWORK_EMOJIS.get(network,"🔗")
    await callback_query.message.answer(
        f"✅ <b>{network_emoji} {network.upper()} Network Selected</b>\n\n"
        f"Please send the <b>Contract Address (CA)</b> of the token you want to analyze."
    )

# ---------------- Contract Address Handler ----------------
@dp.message_handler(state=UserState.waiting_for_ca)
async def handle_contract_address(message: types.Message, state: FSMContext):
    ca = message.text.strip()
    user_data = await state.get_data()
    network = user_data.get('selected_network','ethereum')
    # --- Validate the contract address network ---
    supported_networks = ["solana", "bsc", "base", "arbitrum", "ethereum"]
    # Detect the network from Dexscreener
    actual_network = await detect_network_from_dexscreener(ca)

    except Exception as e:
        await message.reply(f"⚠️ Error checking network: {e}")
        return

    if actual_network is None:
        await message.reply("❌ Could not detect this contract on any supported network (DexScreener returned no results).")
        return

    if actual_network != network:
        await message.reply(
            f"❌ The contract belongs to <b>{actual_network.upper()}</b>, "
            f"but you selected <b>{network.upper()}</b>.\n"
            f"Please send the correct CA for {network.upper()}."
        )
        return

    # ------------------ detect actual network via DexScreener ------------------
    actual_network = await detect_network_from_dexscreener(ca)

    if actual_network is None:
        await message.reply("❌ Could not detect this contract address on any supported network (DexScreener returned no matches).")
        return

    # normalize (both are lower-case already)
    if actual_network != network:
        await message.reply(
            f"❌ The contract you sent belongs to <b>{actual_network.upper()}</b>, "
            f"but you selected <b>{network.upper()}</b>.\n"
            f"Please send the correct CA for {network.upper()}."
        )
        return
    # ---------------------------------------------------------------------------

    waiting_msg = await message.answer(f"🔍 <b>Analyzing Token Data...</b>\n<code>{ca}</code>\n⏳ Fetching real-time data...")

    try:
        chain_id = CHAIN_IDS.get(network, network)
        pair_data = await fetch_token_info_auto(chain_id, ca)
        logo_url, token_info, chart_url = create_professional_message(pair_data, network)

        if not token_info:
            await waiting_msg.edit_text("❌ <b>Unable to fetch token info.</b>")
            return

        buttons = []
        if chart_url:
            buttons.append([InlineKeyboardButton("📊 View Live Chart", url=chart_url)])
        buttons.append([InlineKeyboardButton("🚀 Start Trending", callback_data="start_trending")])
        buttons.append([InlineKeyboardButton("🔄 Analyze Another", callback_data=f"select_{network}")])
        buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
                        InlineKeyboardButton("💬 Support", callback_data="support")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        if logo_url:
            img = await resize_image(logo_url)
            if img:
                await waiting_msg.delete()
                await message.answer_photo(photo=img, caption=token_info + POST_FOOTER, reply_markup=keyboard)
            else:
                await waiting_msg.edit_text(token_info + POST_FOOTER, reply_markup=keyboard)
        else:
            await waiting_msg.edit_text(token_info + POST_FOOTER, reply_markup=keyboard)

        # save contract temporarily for activation flow
        await state.update_data(contract_address=ca)
        user_contracts[message.from_user.id] = ca
        await UserState.waiting_for_trend_package.set()

    except Exception as e:
        await waiting_msg.edit_text(f"❌ Error fetching token info: {e}")
        await send_support_log("ERROR", f"Error in handle_contract_address: {e}", {"ca": ca, "trace": traceback.format_exc()})

# ---------------- Start Trending Callback ----------------
@dp.callback_query_handler(lambda c: c.data == "start_trending", state=UserState.waiting_for_trend_package)
async def handle_start_trending(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    network = user_data.get("selected_network","ethereum")
    packages = TRENDING_PACKAGES.get(network,{})

    # Show packages to user
    buttons = [
        [InlineKeyboardButton(f"3H", callback_data="trend_3h")],
        [InlineKeyboardButton(f"12H", callback_data="trend_12h")],
        [InlineKeyboardButton(f"24H", callback_data="trend_24h")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("📦 Select Trending Package:", reply_markup=keyboard)

# ---------------- Handle Trending Selection ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("trend_"), state=UserState.waiting_for_trend_package)
async def handle_trend_package_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    network = user_data.get("selected_network", "ethereum")

    duration_map = {"trend_3h": "3h", "trend_12h": "12h", "trend_24h": "24h"}
    package = callback_query.data
    duration_label = duration_map.get(package, "3h")

    # Get payment info
    payment_wallet = PAYMENT_WALLETS.get(network, "")
    packages = TRENDING_PACKAGES.get(network, {})
    amount = packages.get(duration_label, 0)

    network_emoji = NETWORK_EMOJIS.get(network, "🔗")

    # Store selected package info
    await state.update_data(selected_package=duration_label, payment_amount=amount)

    # Show payment info to user with "Paid" button
    payment_message = (
        f"╔══════════════════════════╗\n"
        f"     <b>💳 PAYMENT DETAILS</b>\n"
        f"╚══════════════════════════╝\n\n"
        f"{network_emoji} <b>Network:</b> {network.upper()}\n"
        f"⏰ <b>Package:</b> {duration_label.upper()}\n"
        f"💰 <b>Amount:</b> {amount} {network.upper()}\n\n"
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃  <b>📝 PAYMENT WALLET</b>      ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n"
        f"<code>{payment_wallet}</code>\n\n"
        f"<b>📌 Instructions:</b>\n"
        f"1️⃣ Send <b>{amount} {network.upper()}</b> to the wallet above\n"
        f"2️⃣ Click the <b>Paid</b> button below when done\n"
    )

    paid_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Paid", callback_data="payment_paid")]
    ])

    await callback_query.message.answer(payment_message, reply_markup=paid_button)
    await UserState.waiting_for_payment.set()

# ---------------- Handle Payment Confirmation ----------------
@dp.callback_query_handler(lambda c: c.data == "payment_paid", state=UserState.waiting_for_payment)
async def handle_payment_paid(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    user_data = await state.get_data()
    network = user_data.get("selected_network", "ethereum")
    contract_address = user_data.get("contract_address", "N/A")
    selected_package = user_data.get("selected_package", "3h")
    payment_amount = user_data.get("payment_amount", 0)

    network_emoji = NETWORK_EMOJIS.get(network, "🔗")
    username = callback_query.from_user.username or "Unknown"
    user_id = callback_query.from_user.id
    user_full_name = callback_query.from_user.full_name or "Unknown"

    # Notify support team with activation button
    try:
        support_notification = (
            f"╔══════════════════════════╗\n"
            f"  <b>🚀 PAYMENT CLAIMED</b>\n"
            f"╚══════════════════════════╝\n\n"
            f"👤 <b>User:</b> {user_full_name} (@{username})\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
            f"{network_emoji} <b>Network:</b> {network.upper()}\n"
            f"📝 <b>Contract:</b> <code>{contract_address}</code>\n"
            f"⏰ <b>Package:</b> {selected_package.upper()}\n"
            f"💰 <b>Amount:</b> {payment_amount} {network.upper()}\n\n"
            f"<b>⚠️ User clicked PAID - Awaiting TX ID</b>"
        )

        # Add activation button for support
        activate_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Activate Trending", callback_data=f"activate_{user_id}_{network}_{selected_package}")]
        ])

        # Send to optional support chat if provided, else to first SUPPORT_ID
        if SUPPORT_CHAT:
            try:
                await bot.send_message(int(SUPPORT_CHAT), support_notification, reply_markup=activate_button)
            except Exception as e:
                logger.warning("Failed to send support notification to SUPPORT_CHAT: %s", e)
                for sid in SUPPORT_IDS:
                    try:
                        await bot.send_message(sid, support_notification, reply_markup=activate_button)
                    except:
                        pass
        else:
            for sid in SUPPORT_IDS:
                try:
                    await bot.send_message(sid, support_notification, reply_markup=activate_button)
                except Exception as e:
                    logger.warning("Could not send notification to support %s: %s", sid, e)
    except Exception as e:
        logger.exception("Error preparing support notification: %s", e)

    # Ask user to send TX ID to support
    user_message = (
        f"✅ <b>Payment Confirmed!</b>\n\n"
        f"📩 <b>Next Step:</b>\n"
        f"Please send your <b>Transaction ID (TX ID)</b> to our support team for verification.\n\n"
        f"💬 <b>Send TX ID to:</b> @OmniTrendingPortal\n\n"
        f"After verification, your trending will be activated!"
    )

    await callback_query.message.answer(user_message)
    await state.finish()

# ---------------- Activate Trending (Support Only) ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("activate_"))
async def handle_activate_trending(callback_query: types.CallbackQuery):
    """Support-only activation: create channel post, start monitor task."""
    # authorize
    if callback_query.from_user.id not in SUPPORT_IDS:
        await callback_query.answer("🚫 You are not authorized to activate trends.", show_alert=True)
        return

    await callback_query.answer()

    # Parse callback data: activate_{user_id}_{network}_{package}
    parts = callback_query.data.split("_")
    if len(parts) < 4:
        await callback_query.message.answer("❌ Invalid activation data.")
        return

    try:
        target_user_id = int(parts[1])
        network = parts[2]
        package = parts[3]  # e.g., "3h", "12h", "24h"
    except Exception as e:
        await callback_query.message.answer(f"❌ Failed to parse activation data: {e}")
        return

    # Determine duration
    duration_map = {"3h": 3, "12h": 12, "24h": 24}
    hours = duration_map.get(package.lower(), 3)
    duration = timedelta(hours=hours)
    end_time = datetime.utcnow() + duration

    # Recover contract address from user's FSM storage
    async with dp.current_state(user=target_user_id).proxy() as user_data:
        contract_address = user_data.get("contract_address")

    # fallback to in-memory store
    if not contract_address:
        contract_address = user_contracts.get(target_user_id)

    if not contract_address:
        await callback_query.message.answer("❌ No contract address found for this user (they must analyze a token first).")
        return

    # Fetch initial token info (auto)
    pair_data = await fetch_token_info_auto(CHAIN_IDS.get(network, network), contract_address)
    if not pair_data:
        await callback_query.message.answer("❌ Could not fetch token info from providers.")
        return

    logo_url, token_info, chart_url = create_professional_message(pair_data, network)

    # baseline price (float)
    try:
        baseline = float(pair_data.get('priceUsd') or pair_data.get('price') or 0)
    except:
        baseline = 0.0

    # Compose the "Trending Started" header message text
    base_token = pair_data.get('baseToken', {})
    symbol = base_token.get('symbol', 'TOKEN')
    started_text = (
        f"🔥 <b>TRENDING STARTED FOR {symbol}</b>\n\n"
        f"🪙 <b>Contract:</b> <code>{contract_address}</code>\n"
        f"🌐 <b>Network:</b> {network.upper()}\n"
        f"⏰ <b>Duration:</b> {package.upper()}\n"
        f"💵 <b>Baseline Price:</b> ${baseline}\n\n"
        f"📈 Tracking price action and alerting for new highs and dumps (±10%..±70%)."
        f"{POST_FOOTER}"
    )

    # Prepare channel post buttons
    buttons = []
    if chart_url:
        buttons.append([InlineKeyboardButton("📊 View Chart", url=chart_url)])
    buttons.append([InlineKeyboardButton("🌐 OmniTrending • 100K Monthly Subscribers", url="https://t.me/OmniTrendingPortal")])
    buttons.append([InlineKeyboardButton("⚖️ Safety Report", callback_data=f"report_{contract_address}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Post to channel (photo if logo available)
    try:
        if logo_url:
            img = await resize_image(logo_url)
            if img:
                channel_msg = await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=img,
                    caption=started_text,
                    reply_markup=keyboard
                )
            else:
                channel_msg = await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=started_text,
                    reply_markup=keyboard
                )
        else:
            channel_msg = await bot.send_message(
                chat_id=CHANNEL_ID,
                text=started_text,
                reply_markup=keyboard
            )

        # Try to pin the message in the channel (requires bot admin)
        try:
            await bot.pin_chat_message(CHANNEL_ID, channel_msg.message_id, disable_notification=True)
        except Exception as e:
            logger.info("Pin attempt failed: %s", e)

    except Exception as e:
        await callback_query.message.answer(f"❌ Failed to post to channel: {e}")
        await send_support_log("ERROR", f"Failed to post trending started: {e}", {"contract": contract_address})
        return

    # Build session and store it
    session = {
        "user_id": target_user_id,
        "network": network,
        "contract": contract_address,
        "baseline": baseline,
        "start_time": datetime.utcnow(),
        "end_time": end_time,
        "channel_message": {"chat_id": CHANNEL_ID, "message_id": channel_msg.message_id, "is_photo": bool(logo_url)},
        "chart_url": chart_url,
        "logo_url": logo_url,
        "thresholds_triggered": set(),  # e.g., 'high_10'
        "active": True
    }
    TREND_SESSIONS[channel_msg.message_id] = session

    # Notify user
    try:
        await bot.send_message(
            target_user_id,
            f"🎉 <b>TRENDING ACTIVATED!</b>\n\n"
            f"{NETWORK_EMOJIS.get(network, '')} <b>Network:</b> {network.upper()}\n"
            f"⏰ <b>Duration:</b> {package.upper()}\n\n"
            f"Your token is now live on the OmniTrending Channel! 🚀"
        )
    except Exception as e:
        logger.warning("Failed to notify target user: %s", e)

    # Log to support (activation)
    await send_support_log("INFO", f"Activated trending for {symbol}", {
        "user_id": target_user_id,
        "contract": contract_address,
        "network": network,
        "baseline": baseline,
        "channel_message_id": channel_msg.message_id
    })

    # Update support UI message text for admin in the activation button message
    try:
        await callback_query.message.edit_text(
            callback_query.message.text + f"\n\n✅ <b>Activated by {callback_query.from_user.full_name}</b>"
        )
    except:
        pass

    # Start background monitor task
    asyncio.create_task(monitor_trending_session(channel_msg.message_id))

# ---------------- Monitoring Loop (new integrated) ----------------
async def monitor_trending_session(session_msg_id):
    """Monitor one trending session until end_time; post alerts only when thresholds crossed."""
    session = TREND_SESSIONS.get(session_msg_id)
    if not session:
        return

    try:
        while session["active"] and datetime.utcnow() < session["end_time"]:
            # Fetch latest data
            pair_data = await fetch_token_info_auto(CHAIN_IDS.get(session["network"], session["network"]), session["contract"])
            if pair_data:
                logo_url, token_info, chart_url = create_professional_message(pair_data, session["network"])

                # compute price and percent change vs baseline
                try:
                    current_price = float(pair_data.get('priceUsd') or pair_data.get('price') or 0.0)
                except:
                    current_price = 0.0

                baseline = float(session.get("baseline") or 0.0)
                pct_change = 0.0
                if baseline and current_price:
                    pct_change = ((current_price - baseline) / baseline) * 100.0

                # Prepare updated pinned message caption/text
                caption_extra = f"\n\n<b>Baseline:</b> {baseline}\n<b>Current:</b> {current_price}\n<b>Change:</b> {pct_change:.2f}%"
                caption_with_footer = f"{token_info}{caption_extra}{POST_FOOTER}"

                # edit the main channel post
                try:
                    if session["channel_message"]["is_photo"]:
                        await bot.edit_message_caption(
                            chat_id=session["channel_message"]["chat_id"],
                            message_id=session["channel_message"]["message_id"],
                            caption=caption_with_footer,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton("📊 View Chart", url=session.get("chart_url") or chart_url)],
                                [InlineKeyboardButton("⚖️ Safety Report", callback_data=f"report_{session['contract']}")]
                            ]) if (session.get("chart_url") or chart_url) else None
                        )
                    else:
                        await bot.edit_message_text(
                            chat_id=session["channel_message"]["chat_id"],
                            message_id=session["channel_message"]["message_id"],
                            text=caption_with_footer,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton("📊 View Chart", url=session.get("chart_url") or chart_url)],
                                [InlineKeyboardButton("⚖️ Safety Report", callback_data=f"report_{session['contract']}")]
                            ]) if (session.get("chart_url") or chart_url) else None
                        )
                except Exception as e:
                    logger.debug("Failed to edit channel message: %s", e)

                # Send debug update to support (every poll)
                await send_support_log("DEBUG", f"Update for {pair_data.get('baseToken',{}).get('symbol','TOKEN')}: price={current_price}, change={pct_change:.2f}%", {
                    "contract": session["contract"],
                    "network": session["network"],
                    "current_price": current_price,
                    "pct_change": pct_change,
                    "time": datetime.utcnow().isoformat()
                })

                # Check thresholds for highs and dumps (10..70)
                # For highs
                for th in THRESHOLDS:
                    key = f"high_{th}"
                    if key not in session["thresholds_triggered"]:
                        if pct_change >= th:
                            session["thresholds_triggered"].add(key)
                            await post_threshold_alert(session, pair_data, current_price, pct_change, th, is_high=True)

                # For dumps (negative)
                for th in THRESHOLDS:
                    key = f"dump_{th}"
                    if key not in session["thresholds_triggered"]:
                        if pct_change <= -th:
                            session["thresholds_triggered"].add(key)
                            await post_threshold_alert(session, pair_data, current_price, pct_change, th, is_high=False)

            # small sleep between polls
            await asyncio.sleep(POLL_INTERVAL)

        # session ended
        session["active"] = False
        # notify user and support
        try:
            await bot.send_message(
                session["user_id"],
                "✅ <b>TRENDING COMPLETED!</b>\n\nYour token's trending session has ended. Thanks for using OmniTrending! 🚀"
            )
        except Exception as e:
            logger.warning("Failed to notify user about completion: %s", e)

        # post "Trending Completed" to channel
        try:
            end_text = (
                f"✅ <b>TRENDING ENDED FOR {session['contract']}</b>\n\n"
                f"Thanks for using OmniTrending!\n"
                f"{POST_FOOTER}"
            )
            await bot.send_message(session["channel_message"]["chat_id"], end_text)
        except Exception as e:
            logger.debug("Failed to send trending completed to channel: %s", e)

        # notify support(s)
        complete_msg = {
            "event": "Trending Completed",
            "user_id": session['user_id'],
            "contract": session['contract'],
            "network": session['network'],
            "started": str(session['start_time']),
            "ended": str(session['end_time']),
            "thresholds_triggered": list(session.get("thresholds_triggered", []))
        }
        await send_support_log("INFO", "Trending session completed", complete_msg)

        # Post a short analytics report to support
        try:
            # fetch final pair data
            pair_data = await fetch_token_info_auto(CHAIN_IDS.get(session["network"], session["network"]), session["contract"])
            score = compute_safety_score(pair_data or {})
            flags = quick_honeypot_check(pair_data or {})
            summary = ai_style_summary(pair_data or {}, None)
            report_text = (
                f"📊 <b>Post-Trend Report</b>\n\n"
                f"Contract: <code>{session['contract']}</code>\n"
                f"Network: {session['network']}\n"
                f"Score: {score}\n"
                f"Flags: {', '.join(flags.get('flags',[]))}\n\n"
                f"{summary}"
            )
            for sid in SUPPORT_IDS:
                try:
                    await bot.send_message(sid, report_text, parse_mode="HTML")
                except:
                    pass
            log_alert("trend_completed", session['contract'], complete_msg)
        except Exception as e:
            await send_support_log("ERROR", f"Failed to send post-trend report: {e}", {"contract": session.get("contract")})
    except Exception as e:
        await send_support_log("ERROR", f"Error in monitor_trending_session: {e}", {"session_id": session_msg_id, "trace": traceback.format_exc()})
    finally:
        # cleanup session entry
        if session_msg_id in TREND_SESSIONS:
            del TREND_SESSIONS[session_msg_id]

# ---------------- Threshold Alert Posting (unchanged but logs + summary) ----------------
async def post_threshold_alert(session, pair_data, current_price, pct_change, threshold, is_high=True):
    """Post an alert to the channel with logo + stats when a threshold is crossed."""
    symbol = pair_data.get('baseToken',{}).get('symbol', 'TOKEN')
    name = pair_data.get('baseToken',{}).get('name', '')
    chart_url = session.get("chart_url") or (pair_data.get('pairAddress') and f"https://dexscreener.com/{pair_data.get('chainId')}/{pair_data.get('pairAddress')}")
    logo_url = session.get('logo_url') or pair_data.get('info',{}).get('imageUrl') or pair_data.get('baseToken',{}).get('imageUrl')

    if is_high:
        title = f"🚀 NEW HIGH +{pct_change:.2f}% on {symbol} (≥ +{threshold}%)"
    else:
        title = f"💥 BIG DUMP {pct_change:.2f}% on {symbol} (≤ -{threshold}%)"

    # Build alert message
    msg_text = (
        f"{title}\n\n"
        f"<b>{symbol}</b> • {name}\n"
        f"💵 <b>Price:</b> ${current_price:.8f}\n"
        f"📈 <b>Change vs baseline:</b> {pct_change:.2f}%\n"
    )
    if pair_data.get('liquidity',{}):
        msg_text += f"🌊 <b>Liquidity:</b> {format_number(pair_data.get('liquidity',{}).get('usd',0))}\n"
    if pair_data.get('volume',{}):
        msg_text += f"📊 <b>24h Volume:</b> {format_number(pair_data.get('volume',{}).get('h24',0))}\n"
    if chart_url:
        msg_text += f"\n📊 <a href='{chart_url}'>View chart on DexScreener</a>"

    # include powered by footer
    msg_text += f"\n\n🌐 <b>Powered by OmniTrending</b>{POST_FOOTER}"

    # send photo alert if logo exists
    try:
        if logo_url:
            img = await resize_image(logo_url)
            if img:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=img, caption=msg_text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg_text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=CHANNEL_ID, text=msg_text, parse_mode="HTML")

        # send debug copy to support about this alert
        await send_support_log("ALERT", f"{'HIGH' if is_high else 'DUMP'} triggered for {symbol}", {
            "contract": session["contract"],
            "threshold": threshold,
            "pct_change": pct_change,
            "current_price": current_price
        })
        log_alert("threshold", session["contract"], {"threshold": threshold, "pct_change": pct_change})
    except Exception as e:
        await send_support_log("ERROR", f"Failed to send threshold alert: {e}", {"contract": session.get("contract"), "trace": traceback.format_exc()})

# ---------------- Watchlist & Admin Commands (new) ----------------
@dp.message_handler(commands=['watch_add'], state='*')
async def cmd_watch_add(message: types.Message):
    """Usage: /watch_add <chain> <pair_or_address> [note]  (admin-only)"""
    if message.from_user.id not in SUPPORT_IDS:
        await message.reply("Only support/admins can add watchlist entries.")
        return
    args = message.get_args().split()
    if len(args) < 2:
        await message.reply("Usage: /watch_add <chain> <pair_or_address> [note]")
        return
    chain = args[0].lower()
    pair = args[1]
    note = " ".join(args[2:]) if len(args) > 2 else ""
    add_watchlist(chain, pair, note)
    await message.reply(f"Added {pair} on {chain} to watchlist.")

@dp.message_handler(commands=['watch_remove'], state='*')
async def cmd_watch_remove(message: types.Message):
    if message.from_user.id not in SUPPORT_IDS:
        await message.reply("Only support/admins can remove watchlist entries.")
        return
    pair = message.get_args().strip()
    if not pair:
        await message.reply("Usage: /watch_remove <pair_or_address>")
        return
    remove_watchlist(pair)
    await message.reply(f"Removed {pair} from watchlist (if it existed).")

@dp.message_handler(commands=['watch_list'], state='*')
async def cmd_watch_list(message: types.Message):
    rows = list_watchlist()
    if not rows:
        await message.reply("Watchlist is empty.")
        return
    lines = [f"{r[0]} — {r[1]} — {r[2] or ''} — added {r[3]}" for r in rows]
    # chunk to avoid very long messages
    chunk = "\n".join(lines[:50])
    await message.reply(f"<b>Watchlist (most recent)</b>\n\n{chunk}", parse_mode="HTML")

@dp.message_handler(commands=['token_report'], state='*')
async def cmd_token_report(message: types.Message):
    """Usage: /token_report <chain> <contract>"""
    args = message.get_args().split()
    if len(args) < 2:
        await message.reply("Usage: /token_report <chain> <contract>")
        return
    chain = args[0]
    contract = args[1]
    await message.reply("Fetching token data...")
    pair = await fetch_token_info_auto(CHAIN_IDS.get(chain, chain), contract)
    if not pair:
        await message.reply("Could not fetch token data.")
        return
    score = compute_safety_score(pair)
    flags = quick_honeypot_check(pair).get('flags', [])
    summary = ai_style_summary(pair, None)
    logo = pair.get('info',{}).get('imageUrl') or pair.get('baseToken',{}).get('imageUrl')
    if logo:
        img = await resize_image(logo)
        if img:
            await message.reply_photo(img, caption=f"<b>Safety score:</b> {score}\n<b>Flags:</b> {', '.join(flags)}\n\n{summary}", parse_mode="HTML")
            return
    await message.reply(f"<b>Safety score:</b> {score}\n<b>Flags:</b> {', '.join(flags)}\n\n{summary}", parse_mode="HTML")

@dp.message_handler(commands=['promote_checklist'], state='*')
async def cmd_promote_checklist(message: types.Message):
    text = (
        "Ethical promotion checklist:\n"
        "1. Get an audit or security review.\n"
        "2. Publish contract on a scanner (Etherscan/Solscan) and link it.\n"
        "3. Lock or vest liquidity and publish proof.\n"
        "4. Clear website, tokenomics & team transparency (or explain anonymity).\n"
        "5. Follow CoinGecko / CoinMarketCap listing procedures.\n"
        "6. Use organic community-building (AMAs, partnerships), avoid coordinated buys.\n\n"
        "This checklist is for best practices — it does not guarantee listing or success."
    )
    await message.reply(text)

# ---------------- Safety Report callback ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("report_"))
async def handle_report_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    data = callback_query.data[len("report_"):]
    contract = data
    await callback_query.message.answer("Generating safety report...")
    # try to infer network from message or default to ethereum
    # This is a best-effort; the admin can specify /token_report for deeper checks
    pair = await fetch_token_info_auto("ethereum", contract)
    if not pair:
        pair = await fetch_token_info_auto("solana", contract)
    if not pair:
        await callback_query.message.answer("Could not fetch token info for this contract.")
        return
    score = compute_safety_score(pair)
    flags = quick_honeypot_check(pair).get('flags', [])
    summary = ai_style_summary(pair, None)
    await callback_query.message.answer(f"<b>Safety Report</b>\n\nScore: {score}\nFlags: {', '.join(flags)}\n\n{summary}", parse_mode="HTML")

# ---------------- Main Menu & other handlers (unchanged) ----------------
@dp.callback_query_handler(lambda c: c.data == "main_menu", state='*')
async def handle_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.answer()
    user_first = callback_query.from_user.first_name or "there"
    start_text = f"╔══════════════════════════╗\n  <b>🌟 OMNITRENDING BOT 🌟</b>\n╚══════════════════════════╝\n\n👋 Welcome back, <b>{user_first}</b>!\nSelect a network below to get started! 👇"
    buttons = [
        [InlineKeyboardButton("💜 Solana", callback_data="select_solana")],
        [InlineKeyboardButton("💠 Ethereum", callback_data="select_ethereum")],
        [InlineKeyboardButton("🟡 BSC", callback_data="select_bsc")],
        [InlineKeyboardButton("🧊 Base", callback_data="select_base")],
        [InlineKeyboardButton("⚪ Arbitrum", callback_data="select_arbitrum")],
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await callback_query.message.edit_text(start_text, reply_markup=keyboard)
    except:
        await callback_query.message.answer(start_text, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "show_prices", state='*')
async def handle_show_prices(callback_query: types.CallbackQuery):
    await callback_query.answer()

    prices_text = (
        f"╔══════════════════════════╗\n"
        f"     <b>💰 TRENDING PRICES</b>\n"
        f"╚══════════════════════════╝\n\n"
    )

    for network, emoji in NETWORK_EMOJIS.items():
        packages = TRENDING_PACKAGES.get(network, {})
        prices_text += (
            f"{emoji} <b>{network.upper()}</b>\n"
            f"├ 3H:  {packages.get('3h', 0)} {network.upper()}\n"
            f"├ 12H: {packages.get('12h', 0)} {network.upper()}\n"
            f"└ 24H: {packages.get('24h', 0)} {network.upper()}\n\n"
        )

    prices_text += (
        f"<b>📌 How It Works:</b>\n"
        f"1️⃣ Select a network and provide token CA\n"
        f"2️⃣ Choose trending package duration\n"
        f"3️⃣ Make payment and send TX ID to support\n"
        f"4️⃣ Your token goes trending! 🚀"
    )

    back_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ])

    await callback_query.message.answer(prices_text, reply_markup=back_button)

@dp.callback_query_handler(lambda c: c.data == "support", state='*')
async def handle_support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    support_text = (
        "🛠 <b>OmniTrending Support</b>\n\n"
        "If you need help, contact our team below:\n"
        "📩 <a href='https://t.me/OmniTrendingPortal'>Contact Support</a>\n\n"
        "We'll respond as quickly as possible!"
    )
    await callback_query.message.answer(support_text, disable_web_page_preview=True)

# ---------------- Run Bot ----------------
async def on_startup(dp):
    commands = [
        types.BotCommand(command="/start", description="🏠 Start the bot"),
        types.BotCommand(command="/help", description="📘 How to use the bot"),
        types.BotCommand(command="/watch_list", description="🔎 Show watchlist"),
        types.BotCommand(command="/promote_checklist", description="📋 Ethical promotion checklist")
    ]
    await bot.set_my_commands(commands)
    logger.info("🚀 OmniTrending bot is now running...")
    await send_support_log("INFO", "Bot started", {"time": datetime.utcnow().isoformat()})

@dp.message_handler(commands=['help'], state='*')
async def help_command(message: types.Message):
    help_text = (
        "📘 <b>How OmniTrending Works:</b>\n\n"
        "1️⃣ Choose your preferred blockchain network.\n"
        "2️⃣ Provide a token contract address (CA).\n"
        "3️⃣ The bot fetches live data from DEX sources (pump.fun providers or DexScreener).\n"
        "4️⃣ Use the trending system to create an informative post — the bot will monitor and post updates.\n\n"
        "Need more assistance? Tap <b>Support</b> below."
    )
    await message.answer(help_text)
    from keep_alive import keep_alive  # make sure this import is at the top of main.py

# ==========================================================
# ✅ AUTO-FETCH CONTRACT ADDRESS HANDLER
# ==========================================================
import re


async def detect_network_from_dexscreener(ca: str, supported_networks=None):
    """Detect which chain (chainId string) a contract address belongs to using Dexscreener search API.
    Returns chainId as string (e.g. "ethereum", "bsc", "solana", "base", etc.) or None if not found.
    Accepts optional supported_networks (list) but will prefer matches in that list if provided.
    """
    url = f"https://api.dexscreener.com/latest/dex/search/?q={ca}"
    headers = {"User-Agent": "OmniTrending/1.0 (+https://example.com)"}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    print(f"[Dexscreener] search API HTTP {resp.status} for {ca}")
                    return None

                data = await resp.json()
                if not data:
                    print(f"[Dexscreener] empty search response for {ca}")
                    return None

                pairs = data.get("pairs") or data.get("results") or []
                if not pairs:
                    return None

                # If supported_networks provided, try to find matching chainId
                if supported_networks:
                    for p in pairs:
                        chain = p.get("chainId")
                        if chain and chain in supported_networks:
                            return chain

                # fallback: return the first chainId we see
                first = pairs[0]
                chain_id = first.get("chainId")
                return chain_id

    except Exception as e:
        print(f"[Dexscreener] detect_network error for {ca}: {e}")
        return None


@dp.message_handler(lambda message: re.match(r'^(0x[a-fA-F0-9]{40}|[A-Za-z0-9]{32,44})$', message.text.strip()))
async def handle_contract_auto_fetch(message: types.Message):
    """
    Automatically detects contract addresses sent by users,
    validates them on Dexscreener, and fetches token data.
    """
    ca = message.text.strip()
    await message.answer("🔍 Checking contract address on Dexscreener...")

    # Step 1: Validate CA via Dexscreener
    network = await detect_network_from_dexscreener(ca)
    if not network:
        await message.answer("❌ Invalid CA — no matching data found on Dexscreener.")
        return

    await message.answer(f"✅ Network detected: <b>{network}</b>\nFetching token data...")

    # Step 2: Fetch token data from Dexscreener
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dexscreener.com/latest/dex/tokens/{ca}") as resp:
                dex_data = await resp.json()
    except Exception as e:
        await message.answer(f"⚠️ Failed to fetch from Dexscreener.\nError: {e}")
        return

    # Step 3: Fetch token data from Pump.fun
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pump.fun/api/v1/token/{ca}") as resp:
                pump_data = await resp.json() if resp.status == 200 else None
    except Exception as e:
        pump_data = None
        print(f"[Pump.fun Fetch Error] {e}")

    # Step 4: Send result
    reply = f"✅ <b>Token Address:</b> {ca}\n🌐 <b>Network:</b> {network}\n"

    if dex_data.get("pairs"):
        pair = dex_data["pairs"][0]
        base = pair.get("baseToken", {})
        quote = pair.get("quoteToken", {})
        price = pair.get("priceUsd", "N/A")
        reply += f"💎 <b>{base.get('name')}</b> ({base.get('symbol')})\n💰 <b>Price:</b> ${price}\n"
        reply += f"🪙 <b>Pair:</b> {quote.get('symbol', 'Unknown')}\n"
    else:
        reply += "⚠️ No Dexscreener trading data found.\n"

    if pump_data:
        reply += f"🔥 Pump.fun data found for this token.\n"
    else:
        reply += f"❌ No Pump.fun data found.\n"

    if 'POST_FOOTER' in globals():
        reply += POST_FOOTER

    await message.answer(reply)
# ==========================================================
# ✅ AUTO-FETCH CONTRACT ADDRESS HANDLER (RESTORED)
# ==========================================================
import re

@dp.message_handler(lambda message: re.match(r'^(0x[a-fA-F0-9]{40}|[A-Za-z0-9]{32,44})$', message.text.strip()))
async def handle_contract_auto_fetch(message: types.Message):
    """
    Automatically detects when a user sends a contract address (CA),
    validates it with Dexscreener, and fetches token info using existing functions.
    """
    ca = message.text.strip()
    await message.answer("🔍 Checking contract address on Dexscreener...")

    try:
        # Step 1: Detect network via your existing function
        actual_network = await detect_network_from_dexscreener(ca)
        if not actual_network:
            await message.answer("❌ Invalid CA — no matching data found on Dexscreener.")
            return

        await message.answer(f"✅ Network detected: <b>{actual_network}</b>\nFetching live token data...")

        # Step 2: Try to fetch Pump.fun or Dexscreener token data (you already have these functions)
        token_data = None

        try:
            # Some of your existing code uses pumpportal/pump.fun first, then Dexscreener fallback
            token_data = await fetch_from_dexscreener(ca)
        except Exception as e:
            print(f"[fetch_from_dexscreener Error] {e}")

        if not token_data:
            await message.answer("⚠️ No token data found on Dexscreener or Pump.fun.")
            return

        # Step 3: Build a clean summary message
        pair = token_data.get("pairs", [{}])[0]
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        price = pair.get("priceUsd", "N/A")
        liquidity = pair.get("liquidity", {}).get("usd", "N/A")
        fdv = pair.get("fdv", "N/A")
        chart_url = f"https://dexscreener.com/{pair.get('chainId')}/{pair.get('pairAddress')}" if pair.get("pairAddress") else None

        reply = (
            f"💎 <b>{base_token.get('name', 'Unknown')}</b> ({base_token.get('symbol', '-')})\n"
            f"💰 <b>Price:</b> ${price}\n"
            f"💧 <b>Liquidity:</b> ${liquidity}\n"
            f"🏷️ <b>FDV:</b> ${fdv}\n"
            f"🪙 <b>Pair:</b> {quote_token.get('symbol', '-')}\n"
        )

        if chart_url:
            reply += f"\n📊 <a href='{chart_url}'>View chart on Dexscreener</a>"

        if 'POST_FOOTER' in globals():
            reply += POST_FOOTER

        await message.answer(reply, disable_web_page_preview=False)

    except Exception as e:
        print(f"[CA Handler Error] {e}")
        await message.answer("⚠️ An unexpected error occurred while fetching token data.")


if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
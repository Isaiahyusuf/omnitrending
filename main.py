import os
import aiohttp
import asyncio
from io import BytesIO
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# ---------------- Load Bot Token ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT")  # Telegram chat ID for support (optional)

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not found!")

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
    trending_active = State()

# ---------------- Utils ----------------
async def fetch_token_info(chain_id: str, token_address: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and 'pairs' in data and len(data['pairs']) > 0:
                        chain_pairs = [p for p in data['pairs'] if p.get('chainId','').lower() == chain_id.lower()]
                        if chain_pairs:
                            pair = max(chain_pairs, key=lambda x: float(x.get('liquidity', {}).get('usd',0) or 0))
                            return pair
                        elif data['pairs']:
                            return data['pairs'][0]
    except Exception as e:
        print(f"Error fetching token info: {e}")
    return None

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

async def resize_image(url, size=(128,128)):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                img_bytes = await resp.read()
                img = Image.open(BytesIO(img_bytes))
                img.thumbnail(size)
                bio = BytesIO()
                bio.name = "logo.png"
                img.save(bio, format="PNG")
                bio.seek(0)
                return bio
    except:
        return None

def create_professional_message(pair_data, chain_name):
    if not pair_data:
        return None, None, None
    base_token = pair_data.get('baseToken',{})
    price_usd = pair_data.get('priceUsd','N/A')
    price_change_h24 = pair_data.get('priceChange',{}).get('h24',0)
    price_change_h6 = pair_data.get('priceChange',{}).get('h6',0)
    price_change_h1 = pair_data.get('priceChange',{}).get('h1',0)
    volume_24h = pair_data.get('volume',{}).get('h24',0)
    liquidity = pair_data.get('liquidity',{}).get('usd',0)
    fdv = pair_data.get('fdv',0)
    market_cap = pair_data.get('marketCap',0)
    pair_chain = pair_data.get('chainId','Unknown')
    dex_name = pair_data.get('dexId','Unknown')
    pair_address = pair_data.get('pairAddress','')
    logo_url = pair_data.get('info',{}).get('imageUrl') or base_token.get('imageUrl')

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
        f"<code>{base_token.get('address','N/A')}</code>\n"
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
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(start_text, reply_markup=keyboard)

# ---------------- Network Selection ----------------
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

    waiting_msg = await message.answer(f"🔍 <b>Analyzing Token Data...</b>\n<code>{ca}</code>\n⏳ Fetching real-time data...")

    try:
        chain_id = CHAIN_IDS.get(network, network)
        pair_data = await fetch_token_info(chain_id, ca)
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
                await message.answer_photo(photo=img, caption=token_info, reply_markup=keyboard)
            else:
                await waiting_msg.edit_text(token_info, reply_markup=keyboard)
        else:
            await waiting_msg.edit_text(token_info, reply_markup=keyboard)

        await state.update_data(contract_address=ca)
        await UserState.waiting_for_trend_package.set()

    except Exception as e:
        await waiting_msg.edit_text(f"❌ Error fetching token info: {e}")

# ---------------- Start Trending Callback ----------------
@dp.callback_query_handler(lambda c: c.data == "start_trending", state=UserState.waiting_for_trend_package)
async def handle_start_trending(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    network = user_data.get("selected_network","ethereum")
    username = callback_query.from_user.username or callback_query.from_user.full_name
    packages = TRENDING_PACKAGES.get(network,{})

    # Notify support (if configured)
    if SUPPORT_CHAT:
        try:
            await bot.send_message(SUPPORT_CHAT, f"⚡ <b>Trending Request</b>\nUser: @{username}\nNetwork: {network.upper()}")
        except Exception as e:
            print(f"Could not send notification to support chat: {e}")

    # Show packages to user
    buttons = [
        [InlineKeyboardButton(f"3H - {packages['3h']} {network.upper()}", callback_data="trend_3h")],
        [InlineKeyboardButton(f"12H - {packages['12h']} {network.upper()}", callback_data="trend_12h")],
        [InlineKeyboardButton(f"24H - {packages['24h']} {network.upper()}", callback_data="trend_24h")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("📦 Select Trending Package:", reply_markup=keyboard)

# ---------------- Handle Trending Selection ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("trend_"), state=UserState.waiting_for_trend_package)
async def handle_trend_package_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    duration_map = {"trend_3h":3*3600,"trend_12h":12*3600,"trend_24h":24*3600}
    package = callback_query.data
    duration = duration_map.get(package,3600)
    username = callback_query.from_user.username or callback_query.from_user.full_name

    await callback_query.message.answer(f"✅ Trending started for @{username}.\n⏳ Duration: {package[6:]}")
    await state.update_data(trending_duration=duration)

    # Schedule end notification
    asyncio.create_task(trending_timer(callback_query.from_user.id, duration))
    await state.finish()

async def trending_timer(user_id, duration):
    await asyncio.sleep(duration)
    await bot.send_message(user_id, "⏰ Your trending period has ended. Thank you for using OmniTrending!")

# ---------------- Main Menu ----------------
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
    await callback_query.message.edit_text(start_text, reply_markup=keyboard)

# ---------------- Support Handler ----------------
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
        types.BotCommand(command="start", description="🏠 Start the bot"),
        types.BotCommand(command="help", description="📘 How to use the bot")
    ]
    await bot.set_my_commands(commands)
    print("🚀 OmniTrending bot is now running...")

@dp.message_handler(commands=['help'], state='*')
async def help_command(message: types.Message):
    help_text = (
        "📘 <b>How OmniTrending Works:</b>\n\n"
        "1️⃣ Choose your preferred blockchain network.\n"
        "2️⃣ Provide a token contract address (CA).\n"
        "3️⃣ The bot fetches live data from DEX sources.\n"
        "4️⃣ Use the trending system to boost token visibility.\n\n"
        "Need more assistance? Tap <b>Support</b> below."
    )
    await message.answer(help_text)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
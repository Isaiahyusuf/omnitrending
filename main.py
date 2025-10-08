import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from datetime import datetime, timedelta

API_TOKEN = "YOUR_BOT_TOKEN"
SUPPORT_ID = 8435563121
CHANNEL_ID = -1002919368628  # Channel IDs start with -100

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Track trending sessions
active_trends = {}
user_contracts = {}

# ==============================
# 📡 FETCH DATA FROM DEXSCREENER
# ==============================
def get_dexscreener_data(ca):
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        res = requests.get(url).json()
        if 'pairs' in res and len(res['pairs']) > 0:
            pair = res['pairs'][0]
            return {
                "name": pair.get("baseToken", {}).get("name"),
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "price": pair.get("priceUsd"),
                "liquidity": pair.get("liquidity", {}).get("usd"),
                "volume": pair.get("volume", {}).get("h24"),
                "url": pair.get("url"),
                "fdv": pair.get("fdv"),
                "chain": pair.get("chainId"),
            }
    except Exception as e:
        logging.error(f"Dexscreener fetch error: {e}")
    return None


# ==========================
# 🧠 INTERNAL UTIL FUNCTIONS
# ==========================
async def send_debug(msg):
    try:
        await bot.send_message(SUPPORT_ID, f"[DEBUG] {msg}")
    except Exception as e:
        logging.error(f"Failed to send debug: {e}")


# =======================
# 🔁 MONITOR TREND STATUS
# =======================
async def monitor_trending(ca, duration, user_id):
    end_time = datetime.now() + timedelta(hours=duration)
    prev_price = None

    while datetime.now() < end_time:
        data = get_dexscreener_data(ca)
        if data:
            price = float(data["price"])
            if prev_price:
                diff = ((price - prev_price) / prev_price) * 100
                if 10 <= abs(diff) <= 70:
                    if diff > 0:
                        text = f"🚀 *NEW HIGH DETECTED* (+{diff:.2f}%)\n\n**{data['name']} (${data['symbol']})**"
                    else:
                        text = f"💀 *NEW DUMP DETECTED* ({diff:.2f}%)\n\n**{data['name']} (${data['symbol']})**"
                    await bot.send_message(CHANNEL_ID, text)
                    await send_debug(f"Posted update: {text}")
            prev_price = price
        await asyncio.sleep(300)  # every 5 minutes

    await bot.send_message(CHANNEL_ID, f"✅ Trending completed for {data['name']} (${data['symbol']})")
    await send_debug(f"Trending completed for {ca}")
    if user_id in active_trends:
        del active_trends[user_id]


# =====================
# ⚙️ COMMAND HANDLERS
# =====================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🧾 Provide CA", callback_data="provide_ca"),
        InlineKeyboardButton("🧹 Clear", callback_data="clear_ca")
    )
    await message.answer(
        "👋 *Welcome to OmniTrending!*\n\n"
        "Track, Trend, and Dominate across chains.\n"
        "Please provide your token contract address to begin 👇",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data == "provide_ca")
async def request_ca(callback: types.CallbackQuery):
    await callback.message.answer("🔹 Send the *token contract address (CA)* below:")
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "clear_ca")
async def clear_contract(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_contracts:
        del user_contracts[user_id]
        await callback.message.answer("🧹 Your saved contract address has been cleared.")
    else:
        await callback.message.answer("⚠️ You don’t have any saved contract address yet.")
    await callback.answer()


@dp.message_handler(lambda message: message.text.startswith("0x"))
async def receive_ca(message: types.Message):
    user_contracts[message.from_user.id] = message.text.strip()
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🚀 Activate Trending", callback_data="activate_trending")
    )
    await message.answer(
        "✅ Contract address saved successfully!\n\n"
        "You can now activate trending for your project below 👇",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data == "activate_trending")
async def cb_activate(callback: types.CallbackQuery):
    fake_message = callback.message
    fake_message.from_user = callback.from_user
    await activate_trending(fake_message)
    await callback.answer()


@dp.message_handler(commands=['activate'])
async def activate_trending(message: types.Message):
    user_id = message.from_user.id

    # ✅ FIX: support/admin can activate even if CA isn't stored locally
    if user_id not in user_contracts:
        if str(message.from_user.id) == str(SUPPORT_ID):
            if len(user_contracts) > 0:
                last_user = list(user_contracts.keys())[-1]
                ca = user_contracts[last_user]
                await message.answer(f"⚙️ Using the latest user CA: `{ca}`")
            else:
                await message.answer(
                    "⚠️ No stored CA found.\n"
                    "Please provide one manually using `/setca <CA>`."
                )
                return
        else:
            await message.answer(
                "❌ No contract address found for this user.\n"
                "Please analyze a token first by sending its CA."
            )
            return
    else:
        ca = user_contracts[user_id]
    # ✅ END FIX

    data = get_dexscreener_data(ca)
    if not data:
        await message.answer("⚠️ Unable to fetch project data from DexScreener.")
        return

    active_trends[user_id] = {"ca": ca, "end": datetime.now() + timedelta(hours=6)}
    info = (
        f"🔥 *Trending Started!*\n\n"
        f"📛 *{data['name']}* (${data['symbol']})\n"
        f"💰 *Price:* ${data['price']}\n"
        f"📊 *Liquidity:* ${data['liquidity']}\n"
        f"📈 *24h Volume:* ${data['volume']}\n"
        f"🧠 *FDV:* ${data['fdv']}\n"
        f"🌐 *Chain:* {data['chain']}\n"
        f"🔗 [View Chart]({data['url']})"
    )
    await bot.send_message(CHANNEL_ID, info, disable_web_page_preview=True)
    await message.answer("✅ Your trending session has been activated successfully.")
    await send_debug(f"Trending started for {ca} by user {user_id}")

    asyncio.create_task(monitor_trending(ca, 6, user_id))


@dp.message_handler(commands=['setca'])
async def set_contract_address(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("❌ Usage: `/setca <contract_address>`")
        return
    ca = parts[1]
    user_id = message.from_user.id

    user_contracts[user_id] = ca
    await message.reply(f"✅ Contract address `{ca}` has been set successfully.")


@dp.message_handler(commands=['status'])
async def status(message: types.Message):
    if message.from_user.id in active_trends:
        trend = active_trends[message.from_user.id]
        remaining = (trend['end'] - datetime.now()).total_seconds() / 3600
        await message.answer(
            f"📊 *Active Trending*\n\n"
            f"CA: `{trend['ca']}`\n"
            f"⏳ Remaining: *{remaining:.1f} hours*"
        )
    else:
        await message.answer("ℹ️ No active trending sessions found.")


# =========================
# 🚀 BOT STARTUP & LAUNCH
# =========================
async def on_startup(dp):
    await send_debug("OmniTrending bot is now running ✅")

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ---------------- Load Bot Token ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Render environment variable

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not found! "
                     "Set it in Render dashboard under Environment Variables.")

# ---------------- Initialize Bot ----------------
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN_V2)
dp = Dispatcher(bot)

# ---------------- /start Command ----------------
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_first = message.from_user.first_name or "there"
    start_text = (
        f"👋 Hello {user_first}!\n\n"
        "Welcome to *OmniTrending* — where all chains meet the hype\\.\n\n"
        "Track, trend, and dominate across Solana, Ethereum, BSC, Base, and Arbitrum\\.\n\n"
        "Choose your network below to get started:"
    )

    buttons = [
        [InlineKeyboardButton("💜 Solana", callback_data="select_sol")],
        [InlineKeyboardButton("💠 Ethereum", callback_data="select_eth")],
        [InlineKeyboardButton("🟡 BSC", callback_data="select_bsc")],
        [InlineKeyboardButton("🧊 Base", callback_data="select_base")],
        [InlineKeyboardButton("⚪ Arbitrum", callback_data="select_arb")],
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(start_text, reply_markup=keyboard)

# ---------------- Network Selection ----------------
@dp.callback_query_handler(lambda c: c.data.startswith("select_"))
async def handle_network_selection(callback_query: types.CallbackQuery):
    await callback_query.answer()
    network = callback_query.data.split("_")[1].capitalize()
    await callback_query.message.answer(
        f"✅ You selected *{network}* network\\.\n\n"
        "Now please send the *Contract Address (CA)* of the token you want to track or trend\\."
    )

# ---------------- Support ----------------
@dp.callback_query_handler(lambda c: c.data == "support")
async def handle_support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    support_text = (
        "🛠 *OmniTrending Support*\n\n"
        "If you need help, contact our team below:\n"
        "📩 [Contact Support](https://t.me/OmniTrendingPortal)\n\n"
        "We’ll respond as quickly as possible!"
    )
    await callback_query.message.answer(support_text, disable_web_page_preview=True)

# ---------------- Contract Address Handler ----------------
@dp.message_handler(lambda message: message.text and (message.text.startswith("0x") or len(message.text) >= 30))
async def handle_contract_address(message: types.Message):
    ca = message.text.strip()
    response = (
        f"🔍 Scanning token data for:\n`{ca}`\n\n"
        "⏳ Please wait while we fetch information from DEX sources..."
    )
    await message.answer(response)
    # TODO: Integrate DexScreener / pump.fun / Moralis API calls here

# ---------------- /help Command ----------------
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = (
        "📘 *How OmniTrending Works:*\n\n"
        "1️⃣ Choose your preferred blockchain network\\.\n"
        "2️⃣ Provide a token contract address \\(CA\\)\\.\n"
        "3️⃣ The bot fetches live data from multiple DEX sources\\.\n"
        "4️⃣ Use the trending system to boost token visibility\\.\n\n"
        "Need more assistance? Tap *Support* below\\."
    )
    await message.answer(help_text)

# ---------------- Run the Bot ----------------
if __name__ == "__main__":
    print("🚀 OmniTrending bot is now running...")
    executor.start_polling(dp, skip_updates=True)

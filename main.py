import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not found!")

# --- Initialize bot and dispatcher ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# --- /start Command ---
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_first = message.from_user.first_name
    start_text = (
        f"👋 Hello {user_first}!\n\n"
        "Welcome to **OmniTrending** — where all chains meet the hype.\n\n"
        "Track, trend, and dominate across Solana, Ethereum, BSC, Base, and Arbitrum.\n\n"
        "Choose your network below to get started:"
    )

    # Inline buttons
    buttons = [
        [InlineKeyboardButton("💜 Solana", callback_data="select_sol")],
        [InlineKeyboardButton("💠 Ethereum", callback_data="select_eth")],
        [InlineKeyboardButton("🟡 BSC", callback_data="select_bsc")],
        [InlineKeyboardButton("🧊 Base", callback_data="select_base")],
        [InlineKeyboardButton("⚪ Arbitrum", callback_data="select_arb")],
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(start_text, reply_markup=keyboard, parse_mode="Markdown")


# --- Network selection handler ---
@dp.callback_query_handler(lambda c: c.data.startswith("select_"))
async def handle_network_selection(callback_query: types.CallbackQuery):
    network = callback_query.data.split("_")[1].capitalize()
    await callback_query.message.answer(
        f"✅ You selected **{network}** network.\n\n"
        "Now please send the **Contract Address (CA)** of the token you want to track or trend.",
        parse_mode="Markdown"
    )


# --- Support handler ---
@dp.callback_query_handler(lambda c: c.data == "support")
async def handle_support(callback_query: types.CallbackQuery):
    support_text = (
        "🛠 **OmniTrending Support**\n\n"
        "If you need help, contact our team below:\n"
        "📩 [Contact Support](https://t.me/OmniTrendingPortal)\n\n"
        "We’ll respond as quickly as possible!"
    )
    await callback_query.message.answer(support_text, parse_mode="Markdown", disable_web_page_preview=True)


# --- CA message handler ---
@dp.message_handler(lambda message: message.text.startswith("0x") or len(message.text) >= 30)
async def handle_contract_address(message: types.Message):
    ca = message.text.strip()
    response = (
        f"🔍 Scanning token data for:\n`{ca}`\n\n"
        "⏳ Please wait while we fetch information from DEX sources..."
    )
    await message.answer(response, parse_mode="Markdown")
    # TODO: Connect API call to DexScreener / pump.fun / Moralis here


# --- /help Command ---
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = (
        "📘 **How OmniTrending Works:**\n\n"
        "1️⃣ Choose your preferred blockchain network.\n"
        "2️⃣ Provide a token contract address (CA).\n"
        "3️⃣ The bot fetches live data from multiple DEX sources.\n"
        "4️⃣ Use the trending system to boost token visibility.\n\n"
        "Need more assistance? Tap **Support** below."
    )
    await message.answer(help_text, parse_mode="Markdown")


# --- Run the bot ---
if __name__ == "__main__":
    print("🚀 OmniTrending bot is now running...")
    executor.start_polling(dp, skip_updates=True)

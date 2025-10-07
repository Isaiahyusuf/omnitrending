# main.py
# Stage 1 OmniTrending Telegram bot (basic UI + CA input + mock token lookup)
# Requirements: python-telegram-bot, requests, python-dotenv (see requirements.txt)
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
import os
import logging
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory user state (for Stage 1). For production move to DB.
USER_STATE = {}  # user_id -> {"state": "...", "network": "...", "last_ca": "..."}

NETWORKS = {
    "select_sol": "Solana",
    "select_eth": "Ethereum",
    "select_bsc": "BNB Chain",
    "select_base": "Base",
    "select_arb": "Arbitrum",
    "select_all": "All Networks",
}

SUPPORT_LINK = "https://t.me/OmniTrendingSupport"  # change if you have different link

def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start", callback_data="start_flow"),
         InlineKeyboardButton("💡 How It Works", callback_data="how")],
        [InlineKeyboardButton("🛠️ Support", callback_data="support")]
    ])

def network_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔵 Solana", callback_data="select_sol"),
         InlineKeyboardButton("🟣 Ethereum", callback_data="select_eth")],
        [InlineKeyboardButton("🔴 BNB Chain", callback_data="select_bsc"),
         InlineKeyboardButton("⚡ Base", callback_data="select_base")],
        [InlineKeyboardButton("🌊 Arbitrum", callback_data="select_arb"),
         InlineKeyboardButton("🌐 All Networks", callback_data="select_all")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")]
    ])

def token_action_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 View Full Analytics", callback_data="view_analytics")],
        [InlineKeyboardButton("📢 Trend This Token", callback_data="trend_pay")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_networks")]
    ])

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Pay in SOL", callback_data="pay_sol"),
         InlineKeyboardButton("🪙 Pay in USDT (SOL)", callback_data="pay_usdt_solana")],
        [InlineKeyboardButton("💵 Pay in USDT (ETH)", callback_data="pay_usdt_eth")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_token")]
    ])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start - show main menu"""
    if update.message:
        await update.message.reply_text(
            "👋 Welcome to *OmniTrending* — Track. Trend. Dominate.\n\nChoose an option below:",
            parse_mode="Markdown",
            reply_markup=start_keyboard()
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button presses (callback queries)"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # Start flow -> show networks
    if data == "start_flow":
        await query.edit_message_text("Choose a blockchain network to begin:", reply_markup=network_keyboard())
        return

    # How it works
    if data == "how":
        text = (
            "OmniTrending Stage 1: select a network, paste the token contract address (CA),\n"
            "we fetch token metadata (mock/demo) and show analytics. Payment flow is stubbed for Stage 1."
        )
        await query.edit_message_text(text)
        return

    # Support
    if data == "support":
        await query.edit_message_text(f"Need help? Contact support: {SUPPORT_LINK}")
        return

    # Back to start
    if data == "back_to_start":
        await query.edit_message_text("Main menu:", reply_markup=start_keyboard())
        return

    # network selected
    if data in NETWORKS:
        network = NETWORKS[data]
        USER_STATE[user_id] = {"state": "AWAITING_CA", "network": network, "last_ca": None}
        await query.message.reply_text(
            f"✅ You selected *{network}*.\n\nPlease send the token contract address (CA) now.\n\nExample: `0xabc123...` or Solana address.",
            parse_mode="Markdown"
        )
        return

    # Back to network list
    if data == "back_to_networks":
        await query.edit_message_text("Choose a blockchain network to begin:", reply_markup=network_keyboard())
        return

    # Back to token actions
    if data == "back_to_token":
        await query.edit_message_text("Token actions:", reply_markup=token_action_keyboard())
        return

    # View analytics (stub)
    if data == "view_analytics":
        await query.message.reply_text("📈 Full analytics is coming soon (Stage 2).")
        return

    # Trend this token -> show payment options
    if data == "trend_pay":
        await query.message.reply_text("Choose a payment method to submit your token for trending:", reply_markup=payment_keyboard())
        return

    # Payment options (stub)
    if data.startswith("pay_"):
        # record pending payment in memory (demo)
        state = USER_STATE.get(user_id, {})
        ca = state.get("last_ca", "<unknown>")
        network = state.get("network", "<unknown>")
        # In production: create an invoice, provide on-chain address and watch for tx
        await query.message.reply_text(
            f"💳 Payment instructions (demo):\n\n"
            f"Network: {network}\nToken CA: `{ca}`\n\n"
            f"Send the agreed amount to the project wallet. After payment, press ✅ I PAID.\n\n"
            f"(Payment verification will be automatic in a future stage.)",
            parse_mode="Markdown"
        )
        # show a simple "I PAID" button
        paid_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ I PAID (Demo)", callback_data="i_paid")]])
        await query.message.reply_text("When you have sent payment, tap below:", reply_markup=paid_kb)
        return

    if data == "i_paid":
        await query.message.reply_text("Thanks — payment will be verified (demo). We'll queue your token for trending.")
        return

    # unknown callback
    await query.message.reply_text(f"Received unknown action: {data}")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages — used primarily for CA input when awaiting it"""
    msg = update.message
    user_id = msg.from_user.id
    text = msg.text.strip()

    user_state = USER_STATE.get(user_id)
    if not user_state or user_state.get("state") != "AWAITING_CA":
        # Not expecting a CA — provide help
        await msg.reply_text("Send /start to open the OmniTrending menu, or tap Start.")
        return

    # We are expecting a CA
    network = user_state.get("network", "unknown")
    ca = text
    USER_STATE[user_id]["last_ca"] = ca

    await msg.reply_text(f"🔎 Looking up token on *{network}* for CA:\n`{ca}`\n\n(Attempting to fetch data...)", parse_mode="Markdown")

    # fetch token info (best-effort)
    info = fetch_token_info(network, ca)

    # build a friendly project summary
    summary = (
        f"📊 *Token Overview*\n\n"
        f"*Name:* {info.get('name')}\n"
        f"*Symbol:* {info.get('symbol')}\n"
        f"*Price:* {info.get('price')}\n"
        f"*24h Volume:* {info.get('volume_24h')}\n"
        f"*Liquidity:* {info.get('liquidity')}\n"
        f"*Chain:* {network}\n\n"
        f"{info.get('note','')}\n"
        f"{info.get('link','')}"
    )
    await msg.reply_text(summary, parse_mode="Markdown", reply_markup=token_action_keyboard())


def fetch_token_info(network: str, ca: str) -> dict:
    """
    Try to fetch token info from DexScreener (best-effort).
    This is a Stage-1 helper: it attempts to query public endpoints and falls back to a mock.
    Replace / extend this function with proper API calls in Stage 2.
    """
    try:
        # TRY: DexScreener public search endpoint (best-effort)
        query = ca
        url = f"https://api.dexscreener.com/latest/dex/search/?q={query}"
        r = requests.get(url, timeout=8)
        if r.ok:
            data = r.json()
            # DexScreener's response varies. Try to parse a likely structure:
            # If there are results, pick the first pair
            pairs = data.get("pairs") or data.get("pairs", None) or data.get("result", None)
            # defensive parsing:
            if not data:
                raise ValueError("Empty response")
            # Attempt some common fields (many public APIs differ)
            # We'll return partial data where available
            name = data.get("name") or data.get("tokenName") or (ca[:8] + "...")
            symbol = data.get("symbol") or data.get("tokenSymbol") or ""
            price = data.get("priceUsd") or data.get("price") or "N/A"
            volume_24h = data.get("volume24h") or data.get("volume") or "N/A"
            liquidity = data.get("liquidity") or "N/A"
            link = data.get("url") or ""
            return {
                "name": name or ca[:8],
                "symbol": symbol or "",
                "price": price,
                "volume_24h": volume_24h,
                "liquidity": liquidity,
                "link": link,
                "note": "Automated lookup (best-effort). For accurate analytics enable Stage 2 API keys."
            }
    except Exception as e:
        logger.info("Dex lookup failed or unknown format: %s", e)

    # Fallback mock (safe default)
    return {
        "name": "MOCK Token",
        "symbol": "MOCK",
        "price": "$0.0034",
        "volume_24h": "$278,000",
        "liquidity": "$65,000",
        "link": "https://dexscreener.com/",
        "note": "Example data (could not fetch live data). Replace fetch_token_info() with your API in Stage 2."
    }


def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable is required.")
        print("BOT_TOKEN environment variable is required.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_message_handler))

    logger.info("Starting OmniTrending (Stage 1) bot...")
    app.run_polling()

if __name__ == "__main__":
    main()

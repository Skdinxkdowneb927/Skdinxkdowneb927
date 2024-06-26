import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
import requests

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your bot token
my_bot_token = '7365896469:AAFBfHn7OkC2hNUJztrJuFFb-42ugtBpgok'

# Define the channel username
channel_username = '@DZRTGATENOTIFICATIONS'

# Track product availability
product_status = {
    "icy-rush": False,
    "haila": False,
    "samra": False,
    "tamra": False,
    "seaside-frost": False,
    "mint-fusion": False
}

# List of product URLs and their names
products = {
    "icy-rush": "https://www.dzrt.com/en/icy-rush.html",
    "haila": "https://www.dzrt.com/en/haila.html",
    "samra": "https://www.dzrt.com/en/samra.html",
    "tamra": "https://www.dzrt.com/en/tamra.html",
    "seaside-frost": "https://www.dzrt.com/en/seaside-frost.html",
    "mint-fusion": "https://www.dzrt.com/en/mint-fusion.html"
}

# Check product status function
async def check_product_status(context: ContextTypes.DEFAULT_TYPE, initial_run=False):
    for product_name, product_url in products.items():
        try:
            response = requests.get(product_url)
            response.raise_for_status()
            logger.info(f"Fetched {product_name} product page successfully.")

            if "Back In Stock Soon" in response.text:
                product_status[product_name] = False
                logger.info(f"Product {product_name} is out of stock.")
                if initial_run:
                    await context.bot.send_message(
                        chat_id=channel_username,
                        text=f"Product {product_name} is not available. Check it here: {product_url}"
                    )
            else:
                if not product_status[product_name]:
                    product_status[product_name] = True
                    await context.bot.send_message(
                        chat_id=channel_username, 
                        text=f"Product {product_name} is available! Purchase it here: {product_url}"
                    )
                    logger.info(f"Product {product_name} is available and message sent to channel.")
                elif initial_run:
                    await context.bot.send_message(
                        chat_id=channel_username,
                        text=f"Product {product_name} is available. Purchase it here: {product_url}"
                    )
        except Exception as e:
            logger.error(f"Error checking status of product {product_name}: {e}")

# Define start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

    # Schedule the periodic check
    job_removed = remove_job_if_exists("check_product_status", context)
    context.job_queue.run_repeating(check_product_status, interval=15, first=0, name="check_product_status")

    # Initial run to send the current availability status
    await check_product_status(context, initial_run=True)

    text = 'Monitoring started. Checking the product status every 15 seconds.'
    if job_removed:
        text += ' Old job removed.'
    await update.message.reply_text(text)
    logger.info("Bot started and monitoring initialized.")

# Define a test command to send a test message to the channel
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a test message to the channel."""
    await context.bot.send_message(chat_id=channel_username, text="Test message to channel.")
    await update.message.reply_text("Test message sent.")

# Remove existing job
def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(my_bot_token).build()

    # Initialize JobQueue
    job_queue = application.job_queue

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test))

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()

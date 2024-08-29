import os
import helper
from MyOpenAI import MyOpenAI
from GoogleSheetService import GoogleSheetService
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# load .env
load_dotenv()

# save conn
# CONN = helper.connect_db()

# retrieve telegram bot token
TOKEN = os.getenv('TELEGRAM_TOKEN')

# start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(helper.config('telegram.message.start'))

# handle message function
async def handle_message(update: Update, context: CallbackContext) -> None:
    # retrieve message
    message = update.message.text

    await update.message.reply_text(helper.config('telegram.message.waiting_openai'))

    # translate to json using openai
    openai = MyOpenAI()
    openai_response, content = openai.get_response(message)

    # save response on db
    # chat_id = helper.save_openai_response(CONN, openai_response)

    if openai_response is None:
        await update.message.reply_text(helper.config('telegram.message.error_openai'))
    else:
        await update.message.reply_text(helper.config('telegram.message.waiting'))

        try:
            # retrieve clean transactions structure
            transactions = helper.sanitize_response(content)

            if not isinstance(transactions, list) or not transactions:
                await update.message.reply_text(helper.config('telegram.message.error_openai'))
            else:
                # create new GoogleSheetService
                g_sheet_service = GoogleSheetService()

                # loop transactions
                for transaction in transactions:
                    await update.message.reply_text(transaction)

                    # save on db
                    # helper.save_transaction(CONN, transaction, chat_id)
                    # save on google sheets
                    g_sheet_service.add_transaction(transaction)

                await update.message.reply_text(helper.config('telegram.message.success'))

        except Exception as e:
            print(e)
            await update.message.reply_text(helper.config('telegram.message.exception'))

def main():
    # build application
    application = Application.builder().token(TOKEN).build()

    # set start() -> /start
    application.add_handler(CommandHandler('start', start))

    # create handler for all messages (not start with /)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # run bot
    application.run_polling()

if __name__ == '__main__':
    main()
import os
import helper
from services.GoogleSheetService import GoogleSheetService
from services.OpenAIService import OpenAIService
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

# get balance from all bank accounts
async def get_balance(update: Update, context: CallbackContext) -> None:
    # create new GoogleSheetService
    g_sheet_service = GoogleSheetService('get_balance')

    # retrieve bank accounts
    bank_accounts = g_sheet_service.get_balance()

    message_lines = []

    for index, account in enumerate(bank_accounts):
        if account:
            name, amount = account
            print(name, amount)

            if index == len(bank_accounts) - 1:
                message_lines.append(f"<b>{name}: {amount}</b>")
            else:
                message_lines.append(f"{name}: {amount}")

    message = "\n".join(message_lines)

    await update.message.reply_text(message, parse_mode='HTML')

# handle message function
async def handle_message(update: Update, context: CallbackContext) -> None:
    # retrieve message
    message = update.message.text

    await update.message.reply_text(helper.config('telegram.message.waiting_openai'))

    # check permission
    if update.message.from_user.id != int(os.getenv('TELEGRAM_USER_ID')):
        await update.message.reply_text(helper.config('telegram.message.forbidden'))
    else:
        # translate to json using openai
        openai = OpenAIService()
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
                    g_sheet_service = GoogleSheetService('add_transaction')

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

    # set get_balance() -> /get_balance
    application.add_handler(CommandHandler('get_balance', get_balance))

    # create handler for all messages (not start with /)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # run bot
    application.run_polling()

if __name__ == '__main__':
    main()
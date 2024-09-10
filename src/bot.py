import os
import helper
from services.GoogleSheetService import GoogleSheetService
from services.OpenAIService import OpenAIService
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# load .env
load_dotenv()

# save conn
if helper.config('general.db.status'):
    CONN = helper.connect_db()

# retrieve telegram bot token
TOKEN = os.getenv('TELEGRAM_TOKEN')

# set vars
bot_state = {}
trans = {}

# start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(helper.lang(trans, 'telegram.message.start.index'))

# get balance from all bank accounts
async def get_balance(update: Update, context: CallbackContext) -> None:
    # check permission
    if update.message.from_user.id != int(os.getenv('TELEGRAM_USER_ID')):
        await update.message.reply_text(helper.lang(trans, 'telegram.message.forbidden'))
    else:
        if os.getenv('PROTECTED_PASSWORD'):
            # set bot state
            global bot_state
            bot_state = 'waiting_for_password'

            await update.message.reply_text(helper.lang(trans, 'telegram.message.insert_password'))
        else:
            # retrieve and print balance
            await balance(update)

# help function
async def help(update: Update, context: CallbackContext) -> None:
   # retrieve bot commands
    commands = await context.bot.get_my_commands()

    message_lines = []

    for command in commands:
        message_lines.append(f"/{command.command} -> {command.description}")

    message = "\n".join(message_lines)

    await update.message.reply_text(f"Available commands:\n{message}")

# handle message function
async def handle_message(update: Update, context: CallbackContext) -> None:
    # retrieve message
    message = update.message.text
    global bot_state

    # handle different state
    if bot_state == 'waiting_for_password':
        if message == os.getenv('PROTECTED_PASSWORD'):
            # reset bot state
            bot_state = None
            # retrieve and print balance
            await balance(update)
        else:
            await update.message.reply_text(helper.lang(trans, 'telegram.message.error_password'))
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.waiting_openai'))
        # check permission
        if update.message.from_user.id != int(os.getenv('TELEGRAM_USER_ID')):
            await update.message.reply_text(helper.lang(trans, 'telegram.message.forbidden'))
        else:
            # translate to json using openai
            openai = OpenAIService()
            openai_response, content = openai.get_response(message)

            # save response on db
            if helper.config('general.db.status'):
                chat_id = helper.save_openai_response(CONN, openai_response)

            if openai_response is None:
                await update.message.reply_text(helper.lang(trans, 'telegram.message.error_openai'))
            else:
                await update.message.reply_text(helper.lang(trans, 'telegram.message.waiting'))

                try:
                    # retrieve clean transactions structure
                    transactions = helper.sanitize_response(content)

                    if not isinstance(transactions, list) or not transactions:
                        await update.message.reply_text(helper.lang(trans, 'telegram.message.error_openai'))
                    else:
                        # create new GoogleSheetService
                        g_sheet_service = GoogleSheetService('add_transaction')

                        # loop transactions
                        for transaction in transactions:
                            await update.message.reply_text(transaction)

                            # save on db
                            if helper.config('general.db.status'):
                                helper.save_transaction(CONN, transaction, chat_id)

                            # save on google sheets
                            g_sheet_service.add_transaction(transaction)

                        await update.message.reply_text(helper.lang(trans, 'telegram.message.success'))

                except Exception as e:
                    print(e)
                    await update.message.reply_text(helper.lang(trans, 'telegram.message.exception'))

# set suggested commands on "/" in chat
async def post_init(application: Application) -> None:
    command = [
        BotCommand('start','To start something'),
        BotCommand('get_balance','To retrieve balance of bank accounts'),
        BotCommand('build_sheet','Build sheet structure'),
        BotCommand('export','Export sheet in csv'),
        BotCommand('help','To get hints'),
    ]
    await application.bot.set_my_commands(command)

# return balance from gsheet
async def balance(update: Update) -> None:
    # create new GoogleSheetService
    g_sheet_service = GoogleSheetService('get_balance')

    # retrieve bank accounts
    bank_accounts = g_sheet_service.get_balance()

    if isinstance(bank_accounts, list):
        message_lines = []

        for index, account in enumerate(bank_accounts):
            if account:
                name, amount = account

                if index == len(bank_accounts) - 1:
                    message_lines.append(f"\n<b>{name}: {amount}</b>")
                else:
                    message_lines.append(f"{name}: {amount}")

        message = "<tg-spoiler>" + "\n".join(message_lines) + "</tg-spoiler>"

        await update.message.reply_text(message, parse_mode='HTML')
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.exception'))

# build sheet structure
async def build_sheet(update: Update, context: CallbackContext) -> None:
    # create new GoogleSheetService
    g_sheet_service = GoogleSheetService('build_sheet')

    # retrieve bank accounts
    response = g_sheet_service.build_sheet()

    # set message
    message = helper.lang(trans, 'telegram.message.build_sheet.success') if response else helper.lang(trans, 'telegram.message.build_sheet.fail')

    await update.message.reply_text(message)

# export transactions (.csv)
async def export(update: Update, context: CallbackContext) -> None:
    # create new GoogleSheetService
    g_sheet_service = GoogleSheetService('export')

    # retrieve bank accounts
    file_stream = g_sheet_service.export()

    if file_stream:
        # set file name
        file_name = 'export-' + datetime.now().strftime('%d-%m-%Y') + '.csv'
        await context.bot.send_document(chat_id=update.message.chat_id, document=file_stream, filename=file_name)
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.export.fail'))

# export transactions (.csv)
async def set_lang(update: Update, context: CallbackContext) -> None:
    if context.args:
        # retrieve lang param
        lang = context.args[0].lower()
        # set lang on config
        helper.set_lang(lang)
        # load translations
        global trans
        trans = helper.load_translations(helper.config('general.lang'))

        await update.message.reply_text(helper.lang(trans, 'telegram.message.set_lang.success'))
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.set_lang.fail'))

def main():
    # build application
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # set start() -> /start
    application.add_handler(CommandHandler('start', start))

    # set build_sheet() -> /build_sheet
    application.add_handler(CommandHandler('build_sheet', build_sheet))

    # set get_balance() -> /get_balance
    application.add_handler(CommandHandler('get_balance', get_balance))

    # set help() -> /help
    application.add_handler(CommandHandler('help', help))

    # set export() -> /export
    application.add_handler(CommandHandler('export', export))

    # settings
    # application.add_handler(CommandHandler('settings', settings))
    # set settings/set_lang() -> /set_lang
    application.add_handler(CommandHandler('set_lang', set_lang))

    # create handler for all messages (not start with /)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # load translations
    global trans
    trans = helper.load_translations(helper.config('general.lang'))

    # run bot
    application.run_polling()

if __name__ == '__main__':
    main()
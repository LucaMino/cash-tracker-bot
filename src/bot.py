import os
import helper
import pymysql
from database.supabase_api import SupabaseAPI
from services.google_sheet_service import GoogleSheetService
from services.open_ai_service import OpenAIService
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# retrieve and set env vars
TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
CONN = None

# save conn
if helper.config('general.db.status'):
    CONN = helper.connect_db()

# set consts
EXPORT_METHOD = 'generate_export'
# set vars
trans = {}

# start function
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(helper.lang(trans, 'telegram.message.start.index'))

# get balance from all bank accounts
async def get_balance(update: Update, context: CallbackContext) -> None:
    # check permission
    if not TELEGRAM_USER_ID or not helper.user_access(update.message.from_user.id, int(TELEGRAM_USER_ID)):
        await update.message.reply_text(helper.lang(trans, 'telegram.message.forbidden'))
        return
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
    # check permission
    if not TELEGRAM_USER_ID or not helper.user_access(update.message.from_user.id, int(TELEGRAM_USER_ID)):
        await update.message.reply_text(helper.lang(trans, 'telegram.message.forbidden'))
        return
    # retrieve message
    message = update.message.text
    # abort if invalid message
    if not isinstance(message, str): return
    # create openai service
    openai = OpenAIService()
    await update.message.reply_text(helper.lang(trans, 'telegram.message.success_openai'))
    # retrieve method
    method_name = openai.get_method(message)
    method = getattr(openai, method_name)
    # perform method
    openai_response, content = method(message)

    if method_name == EXPORT_METHOD:
        # set file name
        file_name = 'ai-export-' + datetime.now().strftime('%d-%m-%Y') + '.xlsx'
        await context.bot.send_document(chat_id=update.message.chat_id, document=content, filename=file_name)
    else:
        # save response on db
        if helper.config('general.db.status'):
            chat_id = helper.save_openai_response(CONN, openai_response, message)

        if openai_response is None:
            await update.message.reply_text(helper.lang(trans, 'telegram.message.error_openai'))
        else:
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
                        order_message = f"<b>{helper.lang(trans, 'telegram.message.fields.header')}</b>\n\n"

                        for key, value in transaction.items():
                            if key == 'amount':
                                value = f"{value:,.2f} €"
                            row = f"<b>{helper.lang(trans, f'telegram.message.fields.{key}')}</b>: {value}\n"
                            order_message += row

                        await update.message.reply_text(order_message, parse_mode='HTML')

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
        BotCommand('start','To start bot'),
        BotCommand('get_balance','To retrieve balance of bank accounts'),
        # BotCommand('build_sheet','Build sheet structure'),
        BotCommand('export','Export sheet in csv'),
        BotCommand('set_lang','Set default lang [it, en]'),
        BotCommand('help','To get hints'),
    ]

    if isinstance(CONN, (SupabaseAPI, pymysql.connections.Connection)):
        command.append(BotCommand('sync','To sync google sheet with internal database'))

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
    # load translations var global
    global trans
    if context.args:
        # retrieve lang param
        lang = context.args[0].lower()
        # check if lang is available
        if lang not in helper.config('general.available_langs'):
            await update.message.reply_text(helper.lang(trans, 'telegram.message.set_lang.not_available'))
        else:
            # set lang on config
            helper.set_lang(lang)
            # load translations
            trans = helper.load_translations(helper.config('general.lang'))

            await update.message.reply_text(helper.lang(trans, 'telegram.message.set_lang.success'))
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.set_lang.fail'))

# sync google sheet items with database
async def sync(update: Update, context: CallbackContext) -> None:
    # retrieve categories
    g_sheet_service = GoogleSheetService('get_categories')
    categories = g_sheet_service.get_categories()
    # retrieve payment methods
    g_sheet_service = GoogleSheetService('get_payment_methods')
    payment_methods = g_sheet_service.get_payment_methods()
    # check if categories and payment methods are valid
    if isinstance(categories, list) and isinstance(payment_methods, list):
        # load settings
        data = helper.load_settings()
        # set categories
        data['google_sheet']['categories'] = categories
        # set payment methods
        data['google_sheet']['payment_methods'] = payment_methods
        # save settings
        helper.write_settings(data)
        await update.message.reply_text(helper.lang(trans, 'telegram.message.sync.success'))
    else:
        await update.message.reply_text(helper.lang(trans, 'telegram.message.sync.fail'))
# main
def main():
    print('Starting bot...')
    # build application
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # set start() -> /start
    application.add_handler(CommandHandler('start', start))

    # set build_sheet() -> /build_sheet
    # application.add_handler(CommandHandler('build_sheet', build_sheet))

    # set get_balance() -> /get_balance
    application.add_handler(CommandHandler('get_balance', get_balance))

    # set help() -> /help
    application.add_handler(CommandHandler('help', help))

    # set export() -> /export
    application.add_handler(CommandHandler('export', export))

    # set sync() -> /sync
    if isinstance(CONN, (SupabaseAPI, pymysql.connections.Connection)):
        application.add_handler(CommandHandler('sync', sync))

    # set settings/set_lang() -> /set_lang
    application.add_handler(CommandHandler('set_lang', set_lang))

    # create handler for all messages (not start with /)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # load translations
    global trans
    trans = helper.load_translations(helper.config('general.lang'))

    print('Bot started')

    # run bot
    application.run_polling()

if __name__ == '__main__':
    main()

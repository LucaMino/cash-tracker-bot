import re
import os
import json
import io
import pandas as pd
import pymysql
import pymysql.cursors
import xlsxwriter
from typing import Any, Union
from datetime import datetime
from database.supabase_api import SupabaseAPI

# return cleaned response
def sanitize_response(decoded_content: dict) -> list:
    extracted_array = None
    # remove key "transactions" and return only list
    if isinstance(decoded_content, dict):
        for key, value in decoded_content.items():
            if isinstance(value, list):
                extracted_array = value
                break

    if extracted_array is None:
        extracted_array = decoded_content

    required_fields = {'date', 'amount', 'payment_method', 'category', 'note'}

    return [obj for obj in extracted_array if required_fields.issubset(obj.keys())]

# get file path
def get_file_path(name: str = 'settings.json') -> str:
    # absolute path
    current_dir = os.path.dirname(__file__)
    # build settings.json path
    return os.path.join(current_dir, 'config', name)

# load settings.json file
def load_settings() -> dict:
    # build settings.json path
    settings_path = get_file_path()
    # load file
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    # return file content
    return settings

def write_settings(data) -> None:
    # build settings.json path
    settings_path = get_file_path()
    # load file
    with open(settings_path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# retrieve config param from key (settings.json)
def config(key: str) -> Any:
    if '.' in key:
        # return array of splitted keys
        elements = key.split('.')
        # load config file
        settings = load_settings()

        for element in elements:
            # create settings[element1][element2]...
            settings = settings.setdefault(element, {})

        return settings

    return None

# connect db
def connect_db() -> Union[SupabaseAPI, pymysql.connections.Connection]:
    if config('general.db.service') == 'supabase':
        return SupabaseAPI()
    else:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_NAME'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn

# insert db row
def insert_db(conn, table_name, values) -> None:
    # Insert data
    try:
        insert_response = conn.insert(table_name, values)
        print("Insert Response:", insert_response)
    except RuntimeError as e:
        print(e)

# save transaction
def save_transaction(conn, transaction, chat_id) -> None:
    # table
    table_name = "transactions"
    # set values
    values = {
        "category": transaction['category'].lower(),
        "amount": transaction['amount'],
        "payment_method": transaction['payment_method'].lower(),
        "note": transaction['note'].lower(),
        "paid_at": format_db_date(transaction['date']),
        "openai_response_chat_id": chat_id
    }
    # save
    insert_db(conn, table_name, values)

# save openai response
def save_openai_response(conn, response, message) -> int:
    # table
    table_name = "openai_responses"
    # set values
    values = {
        "chat_id": response.id,
        "prompt": message,
        "response": response.choices[0].message.content,
        "completion_tokens": response.usage.completion_tokens,
        "prompt_tokens": response.usage.prompt_tokens,
        "total_tokens": response.usage.total_tokens
    }
    # save
    insert_db(conn, table_name, values)

    return response.id

# load translations
def load_translations(language_code: str) -> dict:
    file_path = f"src/lang/{language_code}/general.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Translation file not found for language: {language_code}")

    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# get the translation string
def lang(translations: dict, key_path: str) -> str:
    keys = key_path.split('.')
    message = translations
    for key in keys:
        message = message.get(key)
        if message is None:
            return None
    return message

# set lang on settings.json
def set_lang(lang: str) -> None:
    # build settings.json path
    settings_path = get_file_path()
    # retrieve file content
    data = load_settings()
    # set new lang
    data['general']['lang'] = lang
    # load file
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# check if the user has permission
def user_access(user_id: int, telegram_user_id: int) -> bool:
    return user_id == int(telegram_user_id)

# create file stream
def create_file_stream(data_string: str) -> io.BytesIO:
    data_io = io.StringIO(data_string)

    df = pd.read_csv(data_io, delimiter=';', skipinitialspace=True)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    return output

# remove any non-numeric characters except for '/'
def format_date(date: str) -> str:
    return re.sub(r'[^0-9/]', '', date)

# convert dd/mm/yyyy to yyyy-mm-dd
def format_db_date(input_date: str) -> str:
    return datetime.strptime(input_date, '%d/%m/%Y').strftime('%Y-%m-%d')
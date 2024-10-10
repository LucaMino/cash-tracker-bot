import os
import json
import io
import pandas as pd
import xlsxwriter
import pymysql
import pymysql.cursors
from datetime import datetime

def sanitize_response(decoded_content):
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
def get_file_path(name = 'settings.json'):
    # absolute path
    current_dir = os.path.dirname(__file__)
    # build settings.json path
    return os.path.join(current_dir, 'config', name)

# load settings.json file
def load_settings():
    # build settings.json path
    settings_path = get_file_path()
    # load file
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    # return file content
    return settings

# retrieve config param from key (settings.json)
def config(key):
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

# convert dd/mm/yyyy to yyyy-mm-dd
def format_db_date(input_date):
    return datetime.strptime(input_date, '%d/%m/%Y').strftime('%Y-%m-%d')

# connect db
def connect_db():
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
def insert_db(conn, sql, values):
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (values))
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")

# save transaction
def save_transaction(conn, transaction, chat_id):
    # create sql script
    sql = "INSERT INTO transactions (category, amount, payment_method, note, paid_at, openai_response_chat_id) VALUES (%s, %s, %s, %s, %s, %s)"
    # set values
    values = [
        transaction['category'].lower(),
        transaction['amount'],
        transaction['payment_method'].lower(),
        transaction['note'].lower(),
        format_db_date(transaction['date']),
        chat_id
    ] #
    # save
    insert_db(conn, sql, values)

# save openai response
def save_openai_response(conn, response):
    # create sql script
    sql = "INSERT INTO openai_responses (chat_id, response, completion_tokens, prompt_tokens, total_tokens) VALUES (%s, %s, %s, %s, %s)"
    # set values
    values = [
        response.id,
        response.choices[0].message.content,
        response.usage.completion_tokens,
        response.usage.prompt_tokens,
        response.usage.total_tokens
    ]
    # save
    insert_db(conn, sql, values)

    return response.id

# load translations
def load_translations(language_code):
    file_path = f"src/lang/{language_code}/general.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Translation file not found for language: {language_code}")

    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def lang(translations, key_path):
    keys = key_path.split('.')
    message = translations
    for key in keys:
        message = message.get(key)
        if message is None:
            return None
    return message

def set_lang(lang):
    # build settings.json path
    settings_path = get_file_path()
    # retrieve file content
    data = load_settings()
    # set new lang
    data['general']['lang'] = lang
    # load file
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def user_access(user_id, telegram_user_id):
    return user_id == int(telegram_user_id)

# create file stream
def create_file_stream(data_string):
    data_io = io.StringIO(data_string)

    df = pd.read_csv(data_io, delimiter=';', skipinitialspace=True)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)

    return output

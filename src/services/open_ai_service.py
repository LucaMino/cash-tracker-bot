import json
import helper
from typing import Any, Optional, Tuple
from datetime import datetime
from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion
from services.google_sheet_service import GoogleSheetService

class OpenAIService:

    def __init__(self):
        self.client = OpenAI()

    def get_method(self, message: str) -> str:
        # set system prompt
        system_prompt = 'Determine whether to use "generate_trans" or "generate_export" based on the request. Return a word "action" (format json)'
        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)
        # validate response
        return content['action']

    def generate_export(self, message: str):
        # set system prompt
        g_sheet_service = GoogleSheetService('export')
        # retrieve csv file content
        csv_content = g_sheet_service.convert_sheet_csv()

        # set system prompt
        system_prompt = f'Given the CSV in array format: {csv_content}. Filter it based on the user\'s prompt and return a JSON with the key: "data" for the final result (which should be a string in CSV format). Do not skip any rows. Consider the first array with Data, Metodo... as the header. The number of columns per row is 5. Use /n for line breaks and separate each cell with a semicolon (;).'

        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)

        # create csv file
        file_stream = helper.create_file_stream(content['data'])

        return response, file_stream

    def generate_trans(self, message: str) -> Tuple[ChatCompletion, Optional[dict]]:
        # set current date
        date = datetime.today().strftime('%d/%m/%Y')
        # retrieve payment_methods and categories from google sheets
        if helper.config('google_sheet.use_gs.categories'):
            g_sheet_service = GoogleSheetService('get_payment_methods')
            payment_methods = g_sheet_service.get_payment_methods()
        else:
            payment_methods = helper.config('google_sheet.payment_methods')

        if helper.config('google_sheet.use_gs.categories'):
            g_sheet_service = GoogleSheetService('get_categories')
            categories = g_sheet_service.get_categories()
        else:
            categories = helper.config('google_sheet.categories')

        # set system prompt
        system_prompt = f'Given the input, return a JSON (can be empty, DO NOT INVENT) with the transactions, each containing: date (dd/mm/yyyy, today: {date}), payment_method (one of [{payment_methods}], default: "Contanti"), category (one of [{categories}]), amount (if expense, negative), note (max 10 characters, not null or set to "-").'

        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)

        return response, content

    def get_response(self, message: str, system_prompt: str) -> Tuple[ChatCompletion, dict]:
        # define messages
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': message
            }
        ]
        try:
            # get response
            response = self.client.chat.completions.create(
                model=helper.config('openai.model'),
                messages=messages,
                max_tokens=helper.config('openai.max_tokens'),
                temperature=helper.config('openai.temperature'),
                response_format=helper.config('openai.response_format'),
            )
            # return message content response
            return response, json.loads(response.choices[0].message.content)

        except OpenAIError as e:
            # handle all OpenAI API errors
            print(f"Error: {e}")
            return None
            raise RuntimeError(f"OpenAI request failed: {e}")
            return None, None
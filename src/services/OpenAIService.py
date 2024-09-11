import json
import helper
from datetime import datetime
from openai import OpenAI, OpenAIError
from services.GoogleSheetService import GoogleSheetService

class OpenAIService:

    def __init__(self):
        self.client = OpenAI()

    def get_method(self, message):
        # set system prompt
        system_prompt = 'Determine whether to use "generate_trans" or "generate_export" based on the request. Return a word "action" (format json)'
        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)
        # validate response
        return content['action']

    def generate_export(self, message):
        # set system prompt
        g_sheet_service = GoogleSheetService('export')
        # retrieve csv file content
        csv_content = g_sheet_service.convert_sheet_csv().getvalue()
        # set system prompt
        system_prompt = f'Data il csv: {csv_content}, converti i dati in formato CSV con la prima riga come header. Ogni riga successiva dovrebbe contenere i valori separati da virgole. Ritorna un json con key: "data" per il CSV (stringa) FILTRATA COME DA INDICAZIONE'
        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)

        print(content['data'])

        # create csv file
        file_stream = helper.create_file_stream(content['data'])

        return response, file_stream

    def generate_trans(self, message):
        # set current date
        date = datetime.today().strftime('%d/%m/%Y')
        # set vars
        categories = helper.config('google_sheet.categories')
        payment_methods = helper.config('google_sheet.payment_methods')
        # set system prompt
        system_prompt = f'Dato l\'input ritorna un json (anche vuoto, NON INVENTARE) con le transazioni, ognuna con: date(dd/mm/yyyy, oggi: {date}), payment_method (one, [{payment_methods}], default: "Contanti"), category (one, [{categories}]), amount(se spesa in negativo), note (max 10 caratteri, not null or set "-")'
        # retrieve gpt response
        response, content = self.get_response(message, system_prompt)

        return response, content

    def get_response(self, message, system_prompt):
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
            # print(response)

            # return message content response
            return response, json.loads(response.choices[0].message.content)

        except OpenAIError as e:
            # handle all OpenAI API errors
            print(f"Error: {e}")
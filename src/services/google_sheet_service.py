import os
import io
import csv
import helper
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetService:
    def __init__(self, func):
        """
        Initializes the Google Sheet Service with the specified function name
        Args:
            func (str): The name of the function to initialize the service for
        """
        # set const
        self.FROM_API = 'FROM API'
        # set scope
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        # check if we are in development or production
        if os.getenv('APP_ENV', 'DEV') == 'DEV':
            # load credentials from file
            credentials = service_account.Credentials.from_service_account_file('src/google-key.json', scopes=scopes)
        else:
            # load credentials from JSON env variable
            credentials = service_account.Credentials.from_service_account_info(json.loads(os.getenv('GOOGLE_KEY_JSON')), scopes=scopes)
        # build service
        self.service = build('sheets', 'v4', credentials=credentials)
        # set range name
        self.range_name = (
            f"{helper.config(f'google_sheet.functions.{func}.sheet_name')}!"
            f"{helper.config(f'google_sheet.functions.{func}.range.total')}"
        )

    def read(self):
        """
        Reads the Google Sheet specified by the range name
        Returns:
            list: A list of rows from the Google Sheet
        """
        # read sheet
        result = self.service.spreadsheets().values().get(spreadsheetId=os.getenv('SPREADSHEET_ID'), range=self.range_name).execute()
        # return values
        return result.get('values', [])

    def write(self, update_range, body):
        """
        Writes to the Google Sheet specified by the update range
        Args:
            update_range (str): The range in the Google Sheet to update
            body (dict): The body of the request containing the values to write
        """
        # add new row
        self.service.spreadsheets().values().update(spreadsheetId=os.getenv('SPREADSHEET_ID'), range=update_range, valueInputOption='RAW', body=body).execute()

    def first_empty_row_index(self):
        """
        Retrieves the index of the first empty row in the Google Sheet
        Returns:
            int: The index of the first empty row
        """
        # retrieve sheet rows
        rows = self.read()
        # return first empty row index
        return len(rows) + 1

    def add_transaction(self, transaction):
        """
        Adds a new transaction to the Google Sheet
        Args:
            transaction (dict): A dictionary containing the transaction details
        """
        # get first empty row
        first_empty_row = self.first_empty_row_index()
        # set update range
        update_range = f"{helper.config('google_sheet.functions.add_transaction.sheet_name')}!{helper.config('google_sheet.functions.add_transaction.range.from')}{first_empty_row}:{helper.config('google_sheet.functions.add_transaction.range.to')}{first_empty_row}"
        # sanitize date
        transaction['date'] = helper.format_date(transaction['date'])
        # set values
        values = [transaction['date'], transaction['payment_method'], transaction['category'], transaction['note'], transaction['amount'], self.FROM_API]
        # set body
        body = { 'values': [values] }
        # write new row
        self.write(update_range, body)

    def get_balance(self):
        """
        Retrieves the balance of bank accounts from the Google Sheet
        Returns:
            list: A list of rows containing the balance information
        """
        try:
            rows = self.read()
            return rows
        except HttpError as err:
            print(err)
            return False

    def get_categories(self):
        """
        Retrieves the categories from the Google Sheet
        Returns:
            list: A list of rows containing the categories
        """
        try:
            rows = self.read()
            clean_rows = [item for subrow in rows for item in subrow]
            return clean_rows
        except HttpError as err:
            print(err)
            return False

    def get_payment_methods(self):
        """
        Retrieves the payment methods from the Google Sheet
        Returns:
            list: A list of rows containing the payment methods
        """
        try:
            rows = self.read()
            clean_rows = [item for subrow in rows for item in subrow]
            return clean_rows
        except HttpError as err:
            print(err)
            return False

    def build_sheet(self):
        """
        Builds the Google Sheet with the header row
        Returns:
            bool: True if the sheet was built successfully, False otherwise
        """
        # set cells
        update_cells = {
            'valueInputOption': 'RAW',
            'data': [
                {
                    'range': self.range_name,
                    'values': [
                        helper.config('google_sheet.header.items')
                    ]
                }
            ]
        }
        # write header row
        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=os.getenv('SPREADSHEET_ID'),
                body=update_cells
            ).execute()
            return True
        except HttpError as err:
            print(err)
            return False

    def convert_sheet_csv(self):
        """
        Converts the Google Sheet to a CSV string
        Returns:
            str: A string containing the CSV data
        """
        # retrieve rows
        rows = self.read()
        return rows

    def export(self):
        """
        Exports the Google Sheet as a CSV file
        Returns:
            io.StringIO: A StringIO object containing the CSV data
        """
        # retrieve rows
        rows = self.read()
        # convert to csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        output.seek(0)

        return output
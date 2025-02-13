import os
from dotenv import load_dotenv
from supabase import create_client, Client

class DatabaseAPI:
    def __init__(self):
        """
        Initializes the database API using configuration from the .env file.
        """
        load_dotenv()

        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)


    def insert(self, table_name: str, data: dict):
        """
        Insert a record into the specified table.

        Args:
            table_name (str): The name of the table to insert data into.
            data (dict): A dictionary representing the record to insert.

        Returns:
            dict: The response from the database.
        """
        try:
            response = self.client.table(table_name).insert(data).execute()
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to insert data into {table_name}: {e}")

    def fetch_all(self, table_name: str):
        """
        Fetch all records from the specified table.

        Args:
            table_name (str): The name of the table to fetch data from.

        Returns:
            dict: The response from the database.
        """
        try:
            response = self.client.table(table_name).select("*").execute()
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from {table_name}: {e}")

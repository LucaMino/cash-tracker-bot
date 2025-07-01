import os
from supabase import create_client, Client
from database.database_interface import DatabaseInterface

class SupabaseAPI(DatabaseInterface):
    def __init__(self):
        """
        Initializes the database API using configuration from the .env file
        """
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            print('Connected to Supabase successfully')
        except Exception as e:
            print(f"Failed to connect to Supabase: {e}")

    def insert(self, table_name, data):
        """
        Insert a record into the specified table
        Args:
            table_name (str): The name of the table to insert data into
            data (dict): A dictionary representing the record to insert
        Returns:
            dict: The response from the database
        """
        try:
            response = self.client.table(table_name).insert(data).execute()
            return response
        except Exception as e:
            raise RuntimeError(f"Failed to insert data into {table_name}: {e}")
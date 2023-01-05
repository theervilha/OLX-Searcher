from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
load_dotenv()

class Database():
    message_table = 'message'
    create_message_table = f"""CREATE TABLE IF NOT EXISTS {message_table} (id serial PRIMARY KEY, chat_id int, context varchar(100), user_message text, bot_response text, created_at_user_message timestamp);"""
    query_insert_messages = f"""INSERT INTO {message_table} (chat_id, context, user_message, bot_response, created_at_user_message) VALUES (%s, %s, %s, %s, %s)"""
    query_select_messages_by_chat_id = f"""SELECT * FROM {message_table} WHERE chat_id = %s"""
    drop_message_table = f"""DELETE FROM {message_table}"""
    
    search_table = 'search'
    create_search_table = f"""CREATE TABLE IF NOT EXISTS {search_table} (id serial PRIMARY KEY, chat_id int, url text, last_time_runned timestamp);"""
    query_select_links_per_user = f"""SELECT chat_id, url, last_time_runned FROM {search_table}"""
    query_select_links_by_chat_id = f"""SELECT chat_id, url, last_time_runned FROM {search_table} WHERE chat_id=%s"""
    query_insert_search = f"""INSERT INTO {search_table} (chat_id, url, last_time_runned) VALUES (%s, %s, %s)"""
    query_update_search_last_time_runned = f"""UPDATE {search_table} SET last_time_runned=%s WHERE chat_id=%s AND url=%s"""
    query_delete_search = f"""DELETE FROM {search_table} WHERE chat_id=%s AND url=%s"""
    drop_search_table = f"""DROP TABLE {search_table}"""
    
    def __init__(self, 
                 host=os.environ.get('database_host'),
                 dbname=os.environ.get('database_name'),
                 user=os.environ.get('database_user'),
                 password=os.environ.get('database_password')
        ):
        print("host:",host)
        print("dbname:",dbname)
        print("user:",user)
        print("password:",password)
        self.conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.create_tables_if_not_exists()
        
    def create_tables_if_not_exists(self):
        self.cur.execute(self.create_message_table)
        self.cur.execute(self.create_search_table)
        self.commit()
    
    def get_messages_by_chat_id(self, chat_id):
        self.cur.execute(self.query_select_messages_by_chat_id % chat_id)
        return self.cur.fetchall()
    
    def insert_messages(self, values):
        self.cur.execute(self.query_insert_messages, values)
        self.commit()
        
    def get_links_per_user(self, chat_id=''):
        if chat_id:
            self.cur.execute(self.query_select_links_by_chat_id % chat_id)
        else:
            self.cur.execute(self.query_select_links_per_user)
            
        return self.cur.fetchall()
    
    def insert_search(self, chat_id, url):
        date = datetime.now().replace(year=1900)
        date -= timedelta(hours=3)
        self.cur.execute(self.query_insert_search, (chat_id, url, date))
        self.commit()
        
    def update_last_time_runned_search(self, chat_id, url):
        date = datetime.now().replace(year=1900)
        date -= timedelta(hours=3)
        self.cur.execute(self.query_update_search_last_time_runned, (date, chat_id, url))
        self.commit()
        
    def delete_search(self, chat_id, url):
        self.cur.execute(self.query_delete_search, (chat_id, url))
        self.commit()
    
    def commit(self):
        self.conn.commit()
    
    def close_db(self):
        self.cur.close()
        self.conn.close()
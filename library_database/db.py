import sqlite3
import json
from pprint import pprint
from firebase import firebase

sqlite_file = 'library.db'    # name of the sqlite database file
table_name = 'BOOKS'  # name of the table to be created

field1 = 'ID' # name of the column
field2 = 'title'
field3 = 'author_fl'
field4 = 'author_code'
field5 = 'language_main'
field6 = 'cover'
field7 = ' available'
field8 = 'collection'

field_type = 'INTEGER'  # column data type

# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()


c.execute('''CREATE TABLE BOOKS(id integer, title text, author_fl text, author_code text, language_main text, cover text, available integer, collection text)''')

with open('books.json') as data_file:
    data = json.load(data_file)
    book_ids = data["books"].keys()
    for key in book_ids:
        book = data["books"][key]
        collections = book['collections']
        typ = ''
        for k in collections.keys():
            typ = collections[k]
        cols = [book['book_id'], book['title'], book['author_fl'], book['author_code'], book['language_main'], book['cover'], 1, typ]
        c.execute("INSERT INTO books VALUES (?,?,?,?,?,?,?,?)", cols)

# Committing changes and closing the connection to the database file
conn.commit()
conn.close()


firebase = firebase.FirebaseApplication('https://your_storage.firebaseio.com', None)
result = firebase.get('/users', None)
print result
{'1': 'John Doe', '2': 'Jane Doe'}







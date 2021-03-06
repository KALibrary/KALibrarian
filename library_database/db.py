import sqlite3
import json

sqlite_file = 'library.db'    # name of the sqlite database file
table_name = 'BOOKS'  # name of the table to be created
# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()


c.execute('''CREATE TABLE BOOKS(id integer, title text, author_fl text, author_code text,
             language_main text, cover text, available integer, collection text)''')

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





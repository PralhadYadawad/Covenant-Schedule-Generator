import sqlite3

conn = sqlite3.connect('schedules.db')
cur = conn.cursor()

for table in ['transactions', 'covenants', 'schedules']:
    print(f'--- {table} ---')
    for row in cur.execute(f'SELECT * FROM {table}'):
        print(row)

conn.close()
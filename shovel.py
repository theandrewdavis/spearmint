import shovel
import sqlite3

@shovel.task
def fixtures():
    fixture_data = [
        ('1/2/2015', '1,000.00', 'Income:Salary', 'A:Checking', 'Salary'),
        ('1/2/2015', '1.00', 'A:Cash', 'E:Food', 'Soda')
    ]

    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('DROP TABLE IF EXISTS transactions')
    cursor.execute('CREATE TABLE transactions (`date` text, `amount` text, `from` text, `to` text, `description` text)')
    cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', fixture_data)
    connection.commit()
    connection.close()
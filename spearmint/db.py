import sqlite3

from . import Account, Transaction

class Database(object):
    database_file = 'db.sqlite3'
    @classmethod
    def create(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS transactions')
        cursor.execute('CREATE TABLE transactions (`date` text, `amount` text, `to` text, `from` text, `description` text)')
        cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', fixture_data)
        connection.commit()
        connection.close()

    @classmethod
    def insert_transactions(cls, transactions):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        tx_tuples = []
        for transaction in transactions:
            tx_tuples.append((transaction.date.strftime('%x'), str(transaction.amount), '', '', transaction.description))
        cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', tx_tuples)
        connection.commit()
        connection.close()

    @classmethod
    def all_transactions(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM transactions')
        transactions = []
        for tx_tuple in cursor.fetchall():
            transactions.append(Transaction(date=tx_tuple[0], amount=tx_tuple[1], description=tx_tuple[2]))
        connection.close()
        return transactions

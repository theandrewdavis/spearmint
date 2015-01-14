import sqlite3

from . import Account, Transaction

class Database(object):
    database_file = 'db.sqlite3'

    @classmethod
    def empty(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS transactions')
        connection.commit()
        connection.close()
        cls.create()

    @classmethod
    def create(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                `tid` text, `date` text, `amount` text, `description` text,
                UNIQUE(tid))''')
        connection.commit()
        connection.close()

    @classmethod
    def merge_transactions(cls, transactions):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        tx_tuples = []
        for transaction in transactions:
            tx_tuples.append((transaction.tid, transaction.date.strftime('%x'), str(transaction.amount), transaction.description))
        cursor.executemany('INSERT OR REPLACE INTO transactions VALUES (?,?,?,?)', tx_tuples)
        connection.commit()
        connection.close()

    @classmethod
    def all_transactions(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM transactions')
        transactions = []
        for tx_tuple in cursor.fetchall():
            transactions.append(Transaction(tid=tx_tuple[0], date=tx_tuple[1], amount=tx_tuple[2], description=tx_tuple[3]))
        connection.close()
        transactions.sort(key=lambda tx: tx.date, reverse=True)
        return transactions

import sqlite3

from . import Account, Transaction

class Database(object):
    database_file = 'db.sqlite3'

    @classmethod
    def empty(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('DROP TABLE IF EXISTS accounts')
        cursor.execute('DROP TABLE IF EXISTS transactions')
        connection.commit()
        connection.close()
        cls.create()

    @classmethod
    def create(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                `id` integer primary key autoincrement, `org` text, `username` text, `number` text, `balance` text,
                UNIQUE(org, username, number))''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                `tid` text, `date` text, `amount` text, `description` text,
                UNIQUE(tid))''')
        connection.commit()
        connection.close()

    @classmethod
    def merge_accounts(cls, accounts):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        for account in accounts:
            account_tuple = (account.org, account.username, account.number, str(account.balance))
            cursor.execute('INSERT OR REPLACE INTO accounts (`org`, `username`, `number`, `balance`) VALUES (?,?,?,?)', account_tuple)
        for account in accounts:
            for transaction in account.transactions:
                tx_tuple = (transaction.tid, transaction.date.strftime('%x'), str(transaction.amount), transaction.description)
                cursor.execute('INSERT OR REPLACE INTO transactions VALUES (?,?,?,?)', tx_tuple)
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

    @classmethod
    def all_accounts(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts')
        accounts = []
        for account_tuple in cursor.fetchall():
            accounts.append(Account(org=account_tuple[1], username=account_tuple[2], number=account_tuple[3], balance=account_tuple[4]))
        connection.close()
        return accounts

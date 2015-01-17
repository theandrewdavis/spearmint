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
                `aid` integer primary key autoincrement, `org` text, `username` text, `number` text, `balance` text,
                UNIQUE(org, username, number))''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                `aid` integer, `tid` text, `date` text, `amount` text, `description` text,
                UNIQUE(aid, tid))''')
        connection.commit()
        connection.close()

    @classmethod
    def merge_statements(cls, statements):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        for statement in statements:
            account_id = cls._upsert_account(cursor, statement.account)
            for transaction in statement.transactions:
                cls._upsert_transaction(cursor, transaction, account_id)
        connection.commit()
        connection.close()

    @classmethod
    def _upsert_account(cls, cursor, account):
        values = (str(account.balance), account.org, account.username, account.number)
        cursor.execute('UPDATE OR IGNORE accounts SET `balance`=? WHERE `org`=? AND `username`=? AND `number`=?', values)
        cursor.execute('INSERT OR IGNORE INTO accounts (`balance`, `org`, `username`, `number`) VALUES (?,?,?,?)', values)
        cursor.execute('SELECT `aid` from accounts WHERE `org`=? AND `username`=? AND `number`=?', values[1:])
        return cursor.fetchone()[0]

    @classmethod
    def _upsert_transaction(cls, cursor, transaction, account_id):
        values = (account_id, transaction.tid, transaction.date.strftime('%x'), str(transaction.amount), transaction.description)
        cursor.execute('INSERT OR REPLACE INTO transactions (`aid`, `tid`, `date`, `amount`, `description`) VALUES (?,?,?,?,?)', values)

    @classmethod
    def all_transactions(cls):
        connection = sqlite3.connect(cls.database_file)
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM transactions')
        transactions = []
        for tx_tuple in cursor.fetchall():
            transactions.append(Transaction(tid=tx_tuple[1], date=tx_tuple[2], amount=tx_tuple[3], description=tx_tuple[4]))
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

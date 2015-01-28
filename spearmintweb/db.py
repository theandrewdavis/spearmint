import json
import sqlite3

from spearmint import Account, Transaction, Login

class LoginView(object):
    def __init__(self, login=None, name=None):
        self.login = login
        self.name = name

    @property
    def name(self):
        if self._name:
            return self._name
        return '{}:{}'.format(self.login.bank, self.login.username)

    @name.setter
    def name(self, value):
        self._name = value

    def upsert(self):
        connection, cursor = Database.open()
        values = (self.login.password, json.dumps(self.login.extra), self._name, self.login.bank, self.login.username)
        cursor.execute('UPDATE OR IGNORE logins SET `password`=?, `extra`=?, `name`=? WHERE `bank`=? AND `username`=?', values)
        cursor.execute('INSERT OR IGNORE INTO logins (`password`, `extra`, `name`, `bank`, `username`) VALUES (?,?,?,?,?)', values)
        Database.close(connection, commit=True)

    @classmethod
    def all(cls):
        connection, cursor = Database.open()
        cursor.execute('SELECT `bank`, `username`, `password`, `extra`, `name` FROM logins')
        login_views = []
        for row in cursor.fetchall():
            login = Login(bank=row[0], username=row[1], password=row[2], extra=json.loads(row[3]))
            login_views.append(LoginView(login=login, name=row[4]))
        Database.close(connection)
        return login_views

    @classmethod
    def from_dict(cls, view_dict):
        return cls(login=Login(**view_dict['login']), name=view_dict['name'])

class Database(object):
    database_file = 'db.sqlite3'

    @classmethod
    def open(cls):
        connection = sqlite3.connect(cls.database_file)
        return (connection, connection.cursor())

    @classmethod
    def close(cls, connection, commit=False):
        if commit:
            connection.commit()
        connection.close()

    @classmethod
    def create_tables(cls):
        connection, cursor = cls.open()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logins (
                `lid` integer primary key autoincrement, `bank` text, `username` text, `password` text, `extra` text, `name` text,
                UNIQUE(bank, username))''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                `aid` integer primary key autoincrement, `org` text, `username` text, `number` text, `balance` text,
                UNIQUE(org, username, number))''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                `aid` integer, `tid` text, `date` text, `amount` text, `description` text,
                UNIQUE(aid, tid))''')
        cls.close(connection, commit=True)

    @classmethod
    def drop_tables(cls):
        connection, cursor = cls.open()
        cursor.execute('DROP TABLE IF EXISTS logins')
        cursor.execute('DROP TABLE IF EXISTS accounts')
        cursor.execute('DROP TABLE IF EXISTS transactions')
        cls.close(connection, commit=True)

    @classmethod
    def merge_statements(cls, statements):
        connection, cursor = cls.open()
        for statement in statements:
            account_id = cls._upsert_account(cursor, statement.account)
            for transaction in statement.transactions:
                cls._upsert_transaction(cursor, transaction, account_id)
        cls.close(connection, commit=True)

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
        connection, cursor = cls.open()
        cursor.execute('SELECT * FROM transactions')
        transactions = []
        for tx_tuple in cursor.fetchall():
            transactions.append(Transaction(tid=tx_tuple[1], date=tx_tuple[2], amount=tx_tuple[3], description=tx_tuple[4]))
        cls.close(connection)
        transactions.sort(key=lambda tx: tx.date, reverse=True)
        return transactions

    @classmethod
    def all_accounts(cls):
        connection, cursor = cls.open()
        cursor.execute('SELECT * FROM accounts')
        accounts = []
        for account_tuple in cursor.fetchall():
            accounts.append(Account(org=account_tuple[1], username=account_tuple[2], number=account_tuple[3], balance=account_tuple[4]))
        cls.close(connection)
        return accounts

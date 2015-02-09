import sqlite3

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
            CREATE TABLE IF NOT EXISTS accounts (
                `aid` integer primary key autoincrement, `org` text, `username` text, `number` text, `balance` text, `name` text,
                UNIQUE(org, username, number))''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                `aid` integer, `tid` text, `date` text, `amount` text, `description` text,
                UNIQUE(aid, tid))''')
        cls.close(connection, commit=True)

    @classmethod
    def drop_tables(cls):
        connection, cursor = cls.open()
        cursor.execute('DROP TABLE IF EXISTS accounts')
        cursor.execute('DROP TABLE IF EXISTS transactions')
        cls.close(connection, commit=True)

    @classmethod
    def from_decimal(cls, value):
        return int(value * 100)

    @classmethod
    def from_date(cls, value):
        return value.strftime('%Y-%m-%d')

class Account(object):
    @classmethod
    def upsert_bank_data(cls, org, username, number, balance):
        connection, cursor = Database.open()
        values = (Database.from_decimal(balance), org, username, number)
        cursor.execute('UPDATE OR IGNORE accounts SET `balance`=? WHERE `org`=? AND `username`=? AND `number`=?', values)
        cursor.execute('INSERT OR IGNORE INTO accounts (`balance`, `org`, `username`, `number`) VALUES (?,?,?,?)', values)
        Database.close(connection, commit=True)

    @classmethod
    def upsert_config_data(cls, org, username, number, name):
        connection, cursor = Database.open()
        values = (name, org, username, number)
        cursor.execute('UPDATE OR IGNORE accounts SET `name`=? WHERE `org`=? AND `username`=? AND `number`=?', values)
        cursor.execute('INSERT OR IGNORE INTO accounts (`name`, `org`, `username`, `number`) VALUES (?,?,?,?)', values)
        Database.close(connection, commit=True)

    @classmethod
    def update(cls, aid, name):
        connection, cursor = Database.open()
        cursor.execute('UPDATE accounts SET `name`=? WHERE `aid`=?', (name, aid))
        Database.close(connection, commit=True)

    @classmethod
    def find_aid(cls, org, username, number):
        connection, cursor = Database.open()
        cursor.execute('SELECT `aid` FROM accounts WHERE `org`=? AND `username`=? AND `number`=?', (org, username, number))
        account_id = cursor.fetchone()[0]
        Database.close(connection)
        return account_id

    @classmethod
    def all(cls):
        connection, cursor = Database.open()
        cursor.execute('SELECT `aid`, `org`, `username`, `number`, `balance`, `name` FROM accounts')
        accounts = []
        for row in cursor.fetchall():
            account = {'aid': row[0], 'org': row[1], 'username': row[2], 'number': row[3], 'balance': row[4], 'name': row[5]}
            accounts.append(account)
        Database.close(connection)
        accounts = sorted(accounts, key=lambda account: abs(int(account['balance'] or 0)), reverse=True)
        return accounts

class Transaction(object):
    @classmethod
    def upsert_bank_data(cls, aid, tid, date, amount, description):
        connection, cursor = Database.open()
        values = (Database.from_date(date), Database.from_decimal(amount), description, aid, tid)
        cursor.execute('UPDATE OR IGNORE transactions SET `date`=?, `amount`=?, `description`=? WHERE `aid`=? AND `tid`=?', values)
        cursor.execute('INSERT OR IGNORE INTO transactions (`date`, `amount`, `description`, `aid`, `tid`) VALUES (?,?,?,?,?)', values)
        Database.close(connection, commit=True)

    @classmethod
    def all(cls):
        connection, cursor = Database.open()
        cursor.execute('SELECT `aid`, `tid`, `date`, `amount`, `description` FROM transactions')
        transactions = []
        for row in cursor.fetchall():
            transaction = {'aid': row[0], 'tid': row[1], 'date': row[2], 'amount': row[3], 'description': row[4]}
            transactions.append(transaction)
        Database.close(connection)
        transactions = sorted(transactions, key=lambda tx: tx['date'], reverse=True)
        return transactions

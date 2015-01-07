import bottle
import sqlite3
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Info needed to fetch all accounts from a bank
class BankInfo(object):
    def __init__(self, **kwargs):
        self.bank = kwargs['bank']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.account_names = kwargs.get('account_names', {})

    # Create array of BankInfos from yaml file
    @staticmethod
    def from_file(filename):
        with open(filename, 'r') as file:
            return [BankInfo(**info) for info in yaml.load(file.read())]

class Account(object):
    def __init__(self, bank_info):
        self.bank_info = bank_info
        self.balance = '0.00'
        self.transactions = []

class Transaction(object):
    @staticmethod
    def from_tuple(tx_tuple):
        transaction = Transaction()
        transaction.date = tx_tuple[0]
        transaction.amount = tx_tuple[1]
        transaction.from_account = tx_tuple[2]
        transaction.to_account = tx_tuple[3]
        transaction.description = tx_tuple[4]
        return transaction

    def to_tuple(self):
        return (self.date, self.amount, self.from_account, self.to_account, self.description)


# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM transactions')
    transactions = [Transaction.from_tuple(row) for row in cursor.fetchall()]
    connection.close()
    return {'transactions': transactions}

# Home page
@bottle.route('/')
def index():
    return bottle.static_file('index.html', root='static')

# Static files
@bottle.route('/<path:path>')
def static(path):
    return bottle.static_file(path, root='static')

# Fetch transactions from web
def fetch(bank_info):
    account = Account(bank_info)
    account.transactions = [
        Transaction.from_tuple(('1/2/2015', '1,000.00', 'Income:Salary', 'A:Checking', 'Salary')),
        Transaction.from_tuple(('1/2/2015', '1.00', 'A:Cash', 'E:Food', 'Soda'))
    ]
    return [account]

# Add transactions from web to database
def merge():
    transactions = []
    for bank in BankInfo.from_file('banks.yaml'):
        for account in fetch(bank):
            for transaction in account.transactions:
                transactions.append(transaction.to_tuple())
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', transactions)
    connection.commit()
    connection.close()

scheduler = BackgroundScheduler()
scheduler.add_job(merge, 'interval', minutes=10)
scheduler.start()
bottle.run(host='localhost', port=8080)

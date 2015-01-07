import bottle
import sqlite3
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Bank details for fetching transactions from web
class BankConfig(object):
    def __init__(self, **kwargs):
        self.bank = kwargs['bank']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.account_names = kwargs.get('account_names', {})

    # Create array of BankConfigs from yaml file
    @staticmethod
    def from_file(filename):
        bank_configs = []
        with open(filename, 'r') as file:
            return [BankConfig(**config) for config in yaml.load(file.read())]

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM transactions')
    transactions = []
    for row in cursor.fetchall():
        transactions.append({'date': row[0], 'amount': row[1], 'from': row[2], 'to': row[3], 'description': row[4]})
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
def fetch(bank_config):
    return [
        {'date': '1/2/2015', 'amount': '1,000.00', 'from': 'Income:Salary', 'to': 'A:Checking', 'description': 'Salary'},
        {'date': '1/2/2015', 'amount': '1.00', 'from': 'A:Cash', 'to': 'E:Food', 'description': 'Soda'}
    ]

# Add transactions from web to database
def merge():
    bank_configs = BankConfig.from_file('banks.yaml')
    transactions = []
    for bank_config in bank_configs:
        for transaction in fetch(bank_config):
            transactions.append((transaction['date'], transaction['amount'], transaction['from'], transaction['to'], transaction['description']))
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', transactions)
    connection.commit()
    connection.close()

scheduler = BackgroundScheduler()
scheduler.add_job(merge, 'interval', minutes=10)
scheduler.start()
bottle.run(host='localhost', port=8080)

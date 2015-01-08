import bottle
import spearmint
import sqlite3
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Add transactions from web to database
def merge():
    # Read bank info from yaml file
    with open('banks.yaml', 'r') as file:
        banks = [spearmint.BankInfo(**info) for info in yaml.load(file.read())]

    # Fetch transactions from web
    transactions = []
    for bank in banks:
        for account in spearmint.fetch(bank):
            for transaction in account.transactions:
                transactions.append(transaction.to_tuple())

    # Write transactions to database
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', transactions)
    connection.commit()
    connection.close()

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM transactions')
    transactions = [spearmint.Transaction.from_tuple(row) for row in cursor.fetchall()]
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

# scheduler = BackgroundScheduler()
# scheduler.add_job(merge, 'interval', minutes=10)
# scheduler.start()
# bottle.run(host='localhost', port=8080)

merge()
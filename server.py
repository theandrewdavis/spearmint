import bottle
import spearmint
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Add transactions from web to database
def merge():
    banks = []
    with open('banks.yaml', 'r') as file:
        for bank_config in yaml.load(file.read()):
            banks.append({'bank': bank_config['bank'], 'username': bank_config['username'], 'password': bank_config['password']})
    transactions = []
    for bank in banks:
        for account in spearmint.fetch(bank=bank['bank'], username=bank['username'], password=bank['password']):
            transactions.extend(account.transactions)
    spearmint.Database.insert_transactions(transactions)

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    tx_json = []
    for transaction in spearmint.Database.all_transactions():
        tx_json.append({
            'date': transaction.date,
            'amount': str(transaction.amount),
            'to': '',
            'from': '',
            'description': transaction.description})
    return {'transactions': tx_json}

# Home page
@bottle.route('/')
def index():
    return bottle.static_file('index.html', root='static')

# Static files
@bottle.route('/<path:path>')
def static(path):
    return bottle.static_file(path, root='static')

scheduler = BackgroundScheduler()
scheduler.add_job(merge, 'interval', minutes=10)
scheduler.start()
bottle.run(host='localhost', port=8080)

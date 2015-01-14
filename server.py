import bottle
import spearmint
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Add transactions from web to database
def merge():
    transactions = []
    logins = spearmint.BankLogin.load('banks.yaml')
    for login in logins:
        for account in spearmint.fetch(login):
            transactions.extend(account.transactions)
    spearmint.Database.merge_transactions(transactions)

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    transactions = [tx.to_object() for tx in spearmint.Database.all_transactions()]
    return {'transactions': transactions}

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

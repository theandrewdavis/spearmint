import bottle
import spearmint
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

# Add transactions from web to database
def merge():
    for login in spearmint.BankLogin.load('banks.yaml'):
        statements = spearmint.fetch(login)
        spearmint.Database.merge_statements(statements)

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    transactions = [tx.as_dict() for tx in spearmint.Database.all_transactions()]
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

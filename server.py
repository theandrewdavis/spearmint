import bottle
import sqlite3

# Transactions as JSON
@bottle.route('/api/transactions')
def api_transactions():
    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM transactions')
    transactions = []
    for row in cursor.fetchall():
        transactions.append({'date': row[0], 'amount': row[1], 'to': row[2], 'from': row[3], 'description': row[4]})
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

bottle.run(host='localhost', port=8080)
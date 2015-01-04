from bottle import route, run, static_file

# Home page
@route('/')
def index():
    return static_file('index.html', root='.')

# Transactions as JSON
@route('/api/transactions')
def api_transactions():
    return {'transactions': [
        {'date': '1/2/2015', 'amount': '2,038.30', 'from': 'Income:NSA', 'to': 'A:Ally', 'description': 'FINANCE AND ACCO FED SALARY~'},
        {'date': '1/2/2015', 'amount': '1.00', 'from': 'A:Cash', 'to': 'E:Food', 'description': 'Soda mess'}
    ]}

run(host='localhost', port=8080)
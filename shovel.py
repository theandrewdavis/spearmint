import shovel
import yaml

# Importing spearmint without adding to sys.path doesn't seem to work in a shovel task
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import spearmint
import spearmintweb

@shovel.task
def server():
    spearmintweb.Server(host='localhost', port=8080).run()

@shovel.task
def empty():
    spearmintweb.Database.drop_tables()
    spearmintweb.Database.create_tables()

@shovel.task
def load_config():
    with open('config.yaml', 'r') as file:
        config = yaml.load(file.read())
        for acct in config['accounts']:
            spearmintweb.Account.upsert_config_data(acct['org'], acct['username'], acct['number'], acct['name'])

def load_logins(bank):
    # Load logins from file
    with open('config.yaml', 'r') as file:
        config = yaml.load(file.read())
        logins = [spearmint.Login(**info) for info in config['logins']]

    # Select specific bank if passed as arg
    if bank is not None:
        logins = [login for login in logins if login.bank == bank]

    if len(logins) == 0:
        raise Exception('No login available for bank {}'.format(bank))

    return logins

def print_data(accounts, transactions):
    for tx in transactions:
        if type(tx) == spearmint.Transaction:
            tx = {'tid': tx.tid, 'date': spearmintweb.Database.from_date(tx.date), 'amount': tx.amount, 'description': tx.description}
        print('{:18.18} {} {:>9} {:.70}'.format(tx['tid'], tx['date'], tx['amount'], tx['description']))
    print('')
    for account in accounts:
        if type(account) == spearmint.Account:
            account = {'org': account.org, 'username': account.username, 'number': account.number, 'balance': account.balance}
        name = account.get('name', None) or '{}:{}:{}'.format(account['org'], account['username'], account['number'])
        print('{:>9} {:100.100}'.format(account['balance'], name))
    print('\n{} transactions, {} accounts\n'.format(len(transactions), len(accounts)))

@shovel.task
def fetch(bank=None):
    logins = load_logins(bank)
    accounts = []
    transactions = []
    for login in logins:
        for statement in spearmint.fetch(login, interactive=True):
            accounts.append(statement.account)
            transactions.extend(statement.transactions)
    print_data(accounts, transactions)

@shovel.task
def merge(bank=None):
    logins = load_logins(bank)
    for login in logins:
        try:
            for statement in spearmint.fetch(login, interactive=True):
                spearmintweb.Updater.merge_statement(statement)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print('Failed to update {}:{}'.format(login.bank, login.username))

@shovel.task
def dump():
    accounts = spearmintweb.Account.all()
    transactions = spearmintweb.Transaction.all()
    print_data(accounts, transactions)

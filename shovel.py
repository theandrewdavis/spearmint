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

@shovel.task
def dump():
    accounts = spearmintweb.Account.all()
    transactions = spearmintweb.Transaction.all()
    for tx in transactions:
        print('{:8} {:>8} {:>9} {}'.format(tx['tid'], tx['date'], tx['amount'], tx['description']))
    print('')
    for account in accounts:
        # print('{:10} {:20} {:20} {:>9}'.format(account['org'], account['username'], account['number'], account['balance']))
        print('{:10} {:>9}'.format(account['name'], account['balance']))
    print('\n{} transactions, {} accounts\n'.format(len(transactions), len(accounts)))


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

@shovel.task
def fetch(bank=None):
    # Fetch accounts and transactions
    logins = load_logins(bank)
    accounts = []
    transactions = []
    for login in logins:
        for statement in spearmint.fetch(login):
            accounts.append(statement.account)
            transactions.extend(statement.transactions)

    # Print accounts and transactions
    for tx in transactions:
        print('{:8} {:>8} {:>9} {}'.format(tx.tid, tx.date.strftime('%x'), tx.amount, tx.description))
    print('')
    for account in accounts:
        print('{:10} {:20} {:20} {:>9}'.format(account.org, account.username, account.number, account.balance))
    print('\n{} transactions, {} accounts\n'.format(len(transactions), len(accounts)))

@shovel.task
def merge(bank=None):
    logins = load_logins(bank)
    for login in logins:
        for statement in spearmint.fetch(login):
            spearmintweb.Updater.merge_statement(statement)

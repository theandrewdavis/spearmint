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
def db_empty():
    spearmintweb.Database.drop_tables()
    spearmintweb.Database.create_tables()

@shovel.task
def db_add_fixtures():
    statements_fixture = [
        spearmint.Statement(
            account=spearmint.Account(org='Citigroup', username='myusername', number='0123456789', balance='123.45'),
            transactions=[
                spearmint.Transaction(tid=1, date='01/02/15', amount='-1,000.00', description='Salary'),
                spearmint.Transaction(tid=2, date='01/03/15', amount='-1.00', description='Soda')
            ]
        ),
        spearmint.Statement(
            account=spearmint.Account(org='Citigroup', username='myusername', number='9876543210', balance='43.21'),
            transactions=[
                spearmint.Transaction(tid=2, date='01/04/15', amount='-2.00', description='Soda')
            ]
        )
    ]
    spearmintweb.Database.merge_statements(statements_fixture)

def print_summary(accounts, transactions):
    for tx in transactions:
        print('{:8} {:>8} {:>9} {}'.format(tx.tid, tx.date.strftime('%x'), tx.amount, tx.description))
    print('')
    for account in accounts:
        print('{:10} {:20} {:20} {:>9}'.format(account.org, account.username, account.number, account.balance))
    print('\n{} transactions, {} accounts\n'.format(len(transactions), len(accounts)))

@shovel.task
def db_dump():
    accounts = spearmintweb.Database.all_accounts()
    transactions = spearmintweb.Database.all_transactions()
    print_summary(accounts, transactions)

@shovel.task
def fetch(bank=None):
    logins = spearmintweb.Login.load('banks.yaml')
    if bank is not None:
        logins = [login for login in logins if login.info['bank'] == bank]
    if len(logins) == 0:
        print('No login available for bank {}'.format(bank))
        return
    accounts = []
    transactions = []
    for login in logins:
        for statement in spearmint.fetch(login.info):
            accounts.append(statement.account)
            transactions.extend(statement.transactions)
    print_summary(accounts, transactions)

@shovel.task
def merge():
    for login in spearmintweb.Login.load('banks.yaml'):
        statements = spearmint.fetch(login.info)
        spearmintweb.Database.merge_statements(statements)

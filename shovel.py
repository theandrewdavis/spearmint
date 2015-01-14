import shovel
import yaml

# Importing spearmint without adding to sys.path doesn't seem to work in a shovel task
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import spearmint

@shovel.task
def db_create():
    spearmint.Database.create()

@shovel.task
def db_empty():
    spearmint.Database.empty()

@shovel.task
def db_dump():
    transactions = spearmint.Database.all_transactions()
    accounts = spearmint.Database.all_accounts()
    for tx in transactions:
        print('{:8} {:>8} {:>9} {}'.format(tx.tid, tx.date.strftime('%x'), tx.amount, tx.description))
    print('')
    for account in accounts:
        print('{:10} {:10} {:10} {:10}'.format(account.org, account.username, account.number, account.balance))
    print('\n{} transactions, {} accounts\n'.format(len(transactions), len(accounts)))

@shovel.task
def db_add_fixtures():
    fixture_data = [
        spearmint.Account(org='Citigroup', username='myusername', number='0123456789', balance='0.00', transactions=[
            spearmint.Transaction(tid=1, date='01/02/15', amount='-1,000.00', description='Salary'),
            spearmint.Transaction(tid=2, date='01/03/15', amount='-1.00', description='Soda')
        ]),
        spearmint.Account(org='Citigroup', username='myusername', number='9876543210', balance='0.00', transactions=[
            spearmint.Transaction(tid=2, date='01/04/15', amount='-2.00', description='Soda')
        ])
    ]
    spearmint.Database.merge_accounts(fixture_data)

@shovel.task
def fetch():
    transactions = []
    for login in spearmint.BankLogin.load('banks.yaml'):
        for account in spearmint.fetch(login):
            transactions.extend(account.transactions)
    for tx in transactions:
        print('{:>8} {:>9} {}'.format(tx.date.strftime('%x'), tx.amount, tx.description))

@shovel.task
def merge():
    for login in spearmint.BankLogin.load('banks.yaml'):
        accounts = spearmint.fetch(login)
        spearmint.Database.merge_accounts(accounts)

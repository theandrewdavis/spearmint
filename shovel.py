import shovel
import yaml

# Importing spearmint without adding to sys.path doesn't seem to work in a shovel task
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import spearmint

@shovel.task
def clear():
    spearmint.Database.create()

@shovel.task
def fixtures():
    fixture_data = [
        spearmint.Transaction(tid=1, date='01/02/15', amount='-1,000.00', description='Salary'),
        spearmint.Transaction(tid=2, date='01/02/15', amount='-1.00', description='Soda')
    ]
    spearmint.Database.merge_transactions(fixture_data)

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
    transactions = []
    logins = spearmint.BankLogin.load('banks.yaml')
    for login in logins:
        for account in spearmint.fetch(login):
            transactions.extend(account.transactions)
    spearmint.Database.merge_transactions(transactions)

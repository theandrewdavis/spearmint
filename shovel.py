import datetime
import shovel
import yaml

# Importing spearmint without adding to sys.path doesn't seem to work in a shovel task
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import spearmint

@shovel.task
def fixtures():
    fixture_data = [
        spearmint.Transaction(date=datetime.datetime(2015, 1, 2), amount='1,000.00', description='Salary'),
        spearmint.Transaction(date=datetime.datetime(2015, 1, 2), amount='1.00', description='Soda')
    ]
    spearmint.Database.create()
    spearmint.Database.insert_transactions(fixture_data)

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
    spearmint.Database.insert_transactions(transactions)

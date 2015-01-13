import datetime
import shovel
import yaml

# Importing spearmint without adding to sys.path doesn't seem to work in a shovel task
# TODO: Figure out why
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
    spearmint.Database.insert_transactions(fixture_data)

@shovel.task
def fetch():
    banks = []
    with open('banks.yaml', 'r') as file:
        for bank_config in yaml.load(file.read()):
            banks.append({'bank': bank_config['bank'], 'username': bank_config['username'], 'password': bank_config['password']})
    transactions = []
    for bank in banks:
        for account in spearmint.fetch(bank=bank['bank'], username=bank['username'], password=bank['password']):
            transactions.extend(account.transactions)
    for tx in transactions:
        print('{:>8} {:>9} {:16} {:16} {}'.format(tx.date.strftime('%x'), tx.amount, tx.from_account, tx.to_account, tx.description))

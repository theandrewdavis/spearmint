import shovel
import sqlite3
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
        ('1/2/2015', '1,000.00', 'Income:Salary', 'A:Checking', 'Salary'),
        ('1/2/2015', '1.00', 'A:Cash', 'E:Food', 'Soda')
    ]

    connection = sqlite3.connect('db.sqlite3')
    cursor = connection.cursor()
    cursor.execute('DROP TABLE IF EXISTS transactions')
    cursor.execute('CREATE TABLE transactions (`date` text, `amount` text, `from` text, `to` text, `description` text)')
    cursor.executemany('INSERT INTO transactions VALUES (?,?,?,?,?)', fixture_data)
    connection.commit()
    connection.close()

@shovel.task
def fetch():
    with open('banks.yaml', 'r') as file:
        banks = [spearmint.BankInfo(**info) for info in yaml.load(file.read())]
    transactions = []
    for bank in banks:
        for account in spearmint.fetch(bank):
            transactions.extend(account.transactions)
    for tx in transactions:
        print('{:>8} {:>9} {:16} {:16} {}'.format(tx.date.strftime('%x'), tx.amount, tx.from_account, tx.to_account, tx.description))

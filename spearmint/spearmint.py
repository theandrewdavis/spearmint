import decimal
import yaml

# TODO: OFX classes should be split into own file, but I need to find a way to avoid circular dependencies
# TODO: Transactions should not store to_account or from_account, that should be in a LedgerEntry or similar
# TODO: Move to/from tuple code out of Transactions, shouldn't need to know about database
# TODO: Create README and move all these TODOs to it

class BankLogin(object):
    def __init__(self, bank=None, username=None, password=None):
        self.bank = bank
        self.username = username
        self.password = password

    @classmethod
    def load(cls, filename):
        logins = []
        with open(filename, 'r') as file:
            for login in yaml.load(file.read()):
                logins.append(cls(bank=login['bank'], username=login['username'], password=login['password']))
        return logins

class Account(object):
    def __init__(self):
        self.balance = decimal.Decimal(0)
        self.transactions = []

class Transaction(object):
    def __init__(self, date=None, amount=None, description=None):
        self.date = date
        self.amount = amount
        self.description = description
        self.to_account = ''
        self.from_account = ''

import decimal

# TODO: OFX classes should be split into own file, but I need to find a way to avoid circular dependencies
# TODO: Transactions should not store to_account or from_account, that should be in a LedgerEntry or similar
# TODO: Remove BankInfo class, these classes should focus on gathering bank data as is, a different class can provide a modified view of it
# TODO: Move to/from tuple code out of Transactions, shouldn't need to know about database
# TODO: Create README and move all these TODOs to it

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

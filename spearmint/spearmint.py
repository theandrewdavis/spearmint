# Info needed to fetch all accounts from a bank
class BankInfo(object):
    def __init__(self, **kwargs):
        self.bank = kwargs['bank']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.account_names = kwargs.get('account_names', {})

class Account(object):
    def __init__(self, bank_info):
        self.bank_info = bank_info
        self.balance = '0.00'
        self.transactions = []

class Transaction(object):
    @classmethod
    def from_tuple(cls, tx_tuple):
        transaction = cls()
        transaction.date = tx_tuple[0]
        transaction.amount = tx_tuple[1]
        transaction.from_account = tx_tuple[2]
        transaction.to_account = tx_tuple[3]
        transaction.description = tx_tuple[4]
        return transaction

    def to_tuple(self):
        return (self.date, self.amount, self.from_account, self.to_account, self.description)

# Fetch transactions from web
def fetch(bank_info):
    if bank_info.bank == 'citi':
        return fetch_citi(bank_info)
    else:
        raise 'Not implemented'

def fetch_citi(bank_info):
    account = Account(bank_info)
    account.transactions = [
        Transaction.from_tuple(('1/2/2015', '1,000.00', 'Income:Salary', 'A:Checking', 'Salary')),
        Transaction.from_tuple(('1/2/2015', '1.00', 'A:Cash', 'E:Food', 'Soda'))
    ]
    return [account]

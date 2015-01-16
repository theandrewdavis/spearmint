import datetime
import decimal
import yaml

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
    def __init__(self, org=None, username=None, number=None, balance=None):
        self.org = org
        self.username = username
        self.number = number
        self.balance = balance

class Transaction(object):
    def __init__(self, tid=None, date=None, amount=None, description=None):
        self.tid = tid
        self.date = self._as_datetime(date)
        self.amount = self._as_decimal(amount)
        self.description = description

    def _as_datetime(self, date):
        if type(date) is datetime.datetime:
            return date
        elif type(date) in [str, unicode]:
            return datetime.datetime.strptime(date, '%x')
        raise 'Invalid date'

    def _as_decimal(self, amount):
        if type(amount) in [str, unicode]:
            return decimal.Decimal(amount.replace(',', ''))
        return decimal.Decimal(amount)

    def as_dict(self):
        return {
            'date': self.date.strftime('%x'),
            'amount': '{:,.2f}'.format(self.amount),
            'description': self.description
        }

class Statement(object):
    def __init__(self, account=None, transactions=[]):
        self.account = account
        self.transactions = transactions

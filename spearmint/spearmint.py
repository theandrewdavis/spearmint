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
    def __init__(self):
        self.balance = decimal.Decimal(0)
        self.transactions = []

class Transaction(object):
    def __init__(self, tid=None, date=None, amount=None, description=None):
        self.tid = tid
        self.date = self._to_datetime(date)
        self.amount = self._to_decimal(amount)
        self.description = description

    def _to_datetime(self, date):
        if type(date) is datetime.datetime:
            return date
        elif type(date) in [str, unicode]:
            return datetime.datetime.strptime(date, '%x')
        raise 'Invalid date'

    def _to_decimal(self, amount):
        if type(amount) in [str, unicode]:
            return decimal.Decimal(amount.replace(',', ''))
        return decimal.Decimal(amount)

    def to_object(self):
        return {
            'date': self.date.strftime('%x'),
            'amount': '{:,.2f}'.format(self.amount),
            'description': self.description
        }
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
    def __init__(self, date=None, amount=None, description=None):
        self.date = self._to_datetime(date)
        self.amount = amount
        self.description = description

    def _to_datetime(self, date):
        if type(date) is datetime.datetime:
            return date
        elif type(date) in [str, unicode]:
            return datetime.datetime.strptime(date, '%x')
        raise 'Invalid date'

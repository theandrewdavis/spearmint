import datetime
import dateutil.parser
import decimal

class Login(object):
    def __init__(self, bank=None, username=None, password=None, extra=None):
        self.bank = bank
        self.username = username
        self.password = password
        self.extra = extra

class Account(object):
    def __init__(self, org=None, username=None, number=None, balance=None):
        self.org = org
        self.username = username
        self.number = number
        self.balance = balance

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        _set_decimal(self, '_balance', value)

class Transaction(object):
    def __init__(self, tid=None, date=None, amount=None, description=None):
        self.tid = tid
        self.date = date
        self.amount = amount
        self.description = description

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        _set_datetime(self, '_date', value)

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        _set_decimal(self, '_amount', value)

class Statement(object):
    def __init__(self, account=None, transactions=None):
        self.account = account
        if transactions is None:
            self.transactions = []
        else:
            self.transactions = transactions

def _set_datetime(obj, attr, value):
    if value is None or type(value) is datetime.datetime:
        setattr(obj, attr, value)
    elif type(value) in [str, unicode]:
        setattr(obj, attr, dateutil.parser.parse(value))
    else:
        raise 'Invalid date'

def _set_decimal(obj, attr, value):
    if value is None:
        setattr(obj, attr, value)
    elif type(value) in [str, unicode]:
        setattr(obj, attr, decimal.Decimal(value.replace(',', '')))
    else:
        setattr(obj, attr, decimal.Decimal(value))

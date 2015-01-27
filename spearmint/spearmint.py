import datetime
import dateutil.parser
import decimal

class SpearmintObject(object):
    def _set_datetime(self, attr, value):
        if value is None or type(value) is datetime.datetime:
            setattr(self, attr, value)
        elif type(value) in [str, unicode]:
            setattr(self, attr, dateutil.parser.parse(value))
        else:
            raise 'Invalid date'

    def _set_decimal(self, attr, value):
        if value is None:
            setattr(self, attr, value)
        elif type(value) in [str, unicode]:
            setattr(self, attr, decimal.Decimal(value.replace(',', '')))
        else:
            setattr(self, attr, decimal.Decimal(value))

class Account(SpearmintObject):
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
        self._set_decimal('_balance', value)

    def as_dict(self):
        return {
            'org': self.org,
            'username': self.username,
            'number': self.number,
            'balance': '{:,.2f}'.format(self.balance)
        }

class Transaction(SpearmintObject):
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
        self._set_datetime('_date', value)

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._set_decimal('_amount', value)

    def as_dict(self):
        return {
            'date': self.date.strftime('%x'),
            'amount': '{:,.2f}'.format(self.amount),
            'description': self.description
        }

class Statement(object):
    def __init__(self, account=None, transactions=None):
        self.account = account
        if transactions is None:
            self.transactions = []
        else:
            self.transactions = transactions

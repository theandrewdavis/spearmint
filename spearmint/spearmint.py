import datetime
import decimal
import ofxparse
import requests
import StringIO
import textwrap
import uuid

# TODO: OFX classes should be split into own file, but I need to find a way to avoid circular dependencies
# TODO: Transactions should not store to_account or from_account, that should be in a LedgerEntry or similar
# TODO: Remove BankInfo class, these classes should focus on gathering bank data as is, a different class can provide a modified view of it
# TODO: Move to/from tuple code out of Transactions, shouldn't need to know about database

# Info needed to fetch all accounts from a bank
class BankInfo(object):
    def __init__(self, **kwargs):
        self.bank = kwargs['bank']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.account_names = kwargs.get('account_names', {})

class Account(object):
    def __init__(self):
        self.balance = decimal.Decimal(0)
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

    def __init__(self, date=None, amount=decimal.Decimal(0), description=''):
        self.date = date
        self.amount = amount
        self.description = description
        self.to_account = ''
        self.from_account = ''

    def to_tuple(self):
        return (self.date.strftime('%x'), str(self.amount), self.from_account, self.to_account, self.description)

class OfxRequest(object):
    @classmethod
    def _template_vars(cls, username, password, org, fid):
        now = datetime.datetime.now()
        start = now - datetime.timedelta(days=30)
        return {
            'fileuid': str(uuid.uuid4()).upper(),
            'time': now.strftime("%Y%m%d%H%M%S"),
            'start': start.strftime("%Y%m%d%H%M%S"),
            'username': username,
            'password': password,
            'org': org,
            'fid': fid
        }

    @classmethod
    def _document(cls, body, template_vars):
        template = """
            OFXHEADER:100
            DATA:OFXSGML
            VERSION:102
            SECURITY:NONE
            ENCODING:USASCII
            CHARSET:1252
            COMPRESSION:NONE
            OLDFILEUID:NONE
            NEWFILEUID:{fileuid}

            <OFX>
            <SIGNONMSGSRQV1>
            <SONRQ>
            <DTCLIENT>{time}
            <USERID>{username}
            <USERPASS>{password}
            <LANGUAGE>ENG
            <FI>
            <ORG>{org}
            <FID>{fid}
            </FI>
            <APPID>QWIN
            <APPVER>1200
            </SONRQ>
            </SIGNONMSGSRQV1>
            {body}
            </OFX>
            """
        template_vars_copy = template_vars.copy()
        template_vars_copy.update({'body': body})
        return cls._process_template(template, template_vars_copy)

    @classmethod
    def _process_template(cls, template, template_vars):
        return textwrap.dedent(template).strip().format(**template_vars)

class OfxAccountsRequest(OfxRequest):
    @classmethod
    def create(cls, username, password, org, fid):
        template_vars = cls._template_vars(username, password, org, fid)
        body = cls._accounts_body(template_vars)
        return cls._document(body, template_vars)

    @classmethod
    def _accounts_body(cls, template_vars):
        template = """
            <SIGNUPMSGSRQV1>
            <ACCTINFOTRNRQ>
            <TRNUID>{time}
            <CLTCOOKIE>1
            <ACCTINFORQ>
            <DTACCTUP>19691231
            </ACCTINFORQ>
            </ACCTINFOTRNRQ>
            </SIGNUPMSGSRQV1>
            """
        return cls._process_template(template, template_vars)

class OfxStatementRequest(OfxRequest):
    @classmethod
    def create(cls, username, password, org, fid, ofxparse_account):
        template_vars = cls._template_vars(username, password, org, fid)
        template_vars['bankid'] = ofxparse_account.routing_number
        template_vars['account'] = ofxparse_account.number
        if ofxparse_account.type == 1:
            template_vars['type'] = 'CHECKING'
            body = cls._bank_statement_body(template_vars)
        elif ofxparse_account.type == 2:
            template_vars['type'] = 'CREDITCARD'
            body = cls._creditcard_statement_body(template_vars)
        else:
            raise Exception('Not implemented')
        return cls._document(body, template_vars)

    @classmethod
    def _bank_statement_body(cls, template_vars):
        template = """
            <BANKMSGSRQV1>
            <STMTTRNRQ>
            <TRNUID>{time}
            <CLTCOOKIE>1
            <STMTRQ>
            <BANKACCTFROM>
            <BANKID>{bankid}
            <ACCTID>{account}
            <ACCTTYPE>{type}
            </BANKACCTFROM>
            <INCTRAN>
            <DTSTART>{start}
            <INCLUDE>Y
            </INCTRAN>
            </STMTRQ>
            </STMTTRNRQ>
            </BANKMSGSRQV1>
            """
        return cls._process_template(template, template_vars)

    @classmethod
    def _creditcard_statement_body(cls, template_vars):
        template = """
            <CREDITCARDMSGSRQV1>
            <CCSTMTTRNRQ>
            <TRNUID>{time}
            <CLTCOOKIE>1
            <CCSTMTRQ>
            <CCACCTFROM>
            <ACCTID>{account}
            </CCACCTFROM>
            <INCTRAN>
            <DTSTART>{start}
            <INCLUDE>Y
            </INCTRAN>
            </CCSTMTRQ>
            </CCSTMTTRNRQ>
            </CREDITCARDMSGSRQV1>
            """
        return cls._process_template(template, template_vars)

class OfxFetcher(object):
    @classmethod
    def fetch(cls, username='', password='', org='', fid='', url=''):
        request = OfxAccountsRequest.create(username, password, org, fid)
        response = cls._post(url, request)
        document = ofxparse.OfxParser.parse(StringIO.StringIO(response))
        accounts = []
        for ofxparse_account in document.accounts:
            request = OfxStatementRequest.create(username, password, org, fid, ofxparse_account)
            response = cls._post(url, request)
            accounts.append(cls._parse_statement(response))
        return accounts


    @classmethod
    def _parse_statement(cls, response):
        document = ofxparse.OfxParser.parse(StringIO.StringIO(response))
        account = Account()
        account.balance = document.account.statement.balance
        for ofxparse_tx in document.account.statement.transactions:
            account.transactions.append(Transaction(
                date=ofxparse_tx.date,
                amount=ofxparse_tx.amount,
                description=ofxparse_tx.payee))
        return account

    @classmethod
    def _post(cls, url, request):
        headers = {'Content-type': 'application/x-ofx', 'Accept': '*/*, application/x-ofx'}
        response = requests.post(url, headers=headers, data=request)
        return response.text

# Fetch transactions from web
def fetch(bank_info):
    if bank_info.bank == 'citi':
        return fetch_citi(bank_info)
    else:
        raise 'Not implemented'

def fetch_citi(bank_info):
    return OfxFetcher.fetch(
        username=bank_info.username,
        password=bank_info.password,
        org='Citigroup',
        fid='24909',
        url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

import datetime
import ofxparse
import requests
import StringIO
import textwrap
import uuid

from . import Account, Transaction, Statement

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
        statements = []
        for ofxparse_account in document.accounts:
            request = OfxStatementRequest.create(username, password, org, fid, ofxparse_account)
            response = cls._post(url, request)
            statements.append(cls._parse_statement(response, org, username))
        return statements

    @classmethod
    def _parse_statement(cls, response, org, username):
        statement = Statement()
        statement.account = Account()
        document = ofxparse.OfxParser.parse(StringIO.StringIO(response))
        statement.account.org = org
        statement.account.username = username
        statement.account.number = document.account.account_id
        statement.account.balance = document.account.statement.balance
        for ofxparse_tx in document.account.statement.transactions:
            statement.transactions.append(Transaction(
                tid=ofxparse_tx.id,
                date=ofxparse_tx.date,
                amount=ofxparse_tx.amount,
                description=ofxparse_tx.payee))
        return statement

    @classmethod
    def _post(cls, url, request):
        headers = {'Content-type': 'application/x-ofx', 'Accept': '*/*, application/x-ofx'}
        response = requests.post(url, headers=headers, data=request)
        return response.text

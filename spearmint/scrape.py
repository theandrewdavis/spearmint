import datetime
import dateutil.parser
import json
import lxml.html
import re
import requests

from . import Account, Statement, Transaction, OfxParser

class ScrapeFetcher(object):
    @classmethod
    def fetch(cls, bank=None, username=None, password=None, questions=None):
        methods = {
            'capitalone360': cls._fetch_capitalone360,
            'ally': cls._fetch_ally,
            'barclay': cls._fetch_barclay,
            'usbank': cls._fetch_usbank
        }
        if bank not in methods:
            raise Exception('Not implemented')
        return methods[bank](username, password, questions)

    @classmethod
    def _fetch_capitalone360(cls, username, password, questions):
        session = requests.Session()

        # Submit username
        url = 'https://secure.capitalone360.com/myaccount/banking/login.vm'
        response = session.post(url, data={'publicUserId': username})

        # Get password form and XSRF token
        url = 'https://secure.capitalone360.com/myaccount/banking/loginauthentication'
        response = session.get(url, params={'execution': 'e1s1', 'stateId': 'collectPassword'})
        html = lxml.html.fromstring(response.text)
        pageToken = html.xpath("//input[@name='pageToken']")[0].get('value')

        # Submit password
        url = 'https://secure.capitalone360.com/myaccount/banking/loginauthentication'
        params = {'execution': 'e1s1'}
        data = {
            '_eventId': 'continue',
            'currentPassword_TLNPI': password,
            'in_dp': ('version%3D2%26pm%5Ffpua%3Dmozilla%2F5%2E0%20%28macintosh%3B%20intel%20mac%20os%20x%2010%5F9'
                '%5F5%29%20applewebkit%2F537%2E36%20%28khtml%2C%20like%20gecko%29%20chrome%2F39%2E0%2E2171%2E95%20'
                'safari%2F537%2E36%7C5%2E0%20%28Macintosh%3B%20Intel%20Mac%20OS%20X%2010%5F9%5F5%29%20AppleWebKit%'
                '2F537%2E36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F39%2E0%2E2171%2E95%20Safari%2F537%2E36%7CMa'
                'cIntel%26pm%5Ffpsc%3D24%7C1680%7C1050%7C1024%26pm%5Ffpsw%3D%26pm%5Ffptz%3D%2D5%26pm%5Ffpln%3Dlang'
                '%3Den%2DUS%7Csyslang%3D%7Cuserlang%3D%26pm%5Ffpjv%3D1%26pm%5Ffpco%3D1%26pm%5Ffpasw%3Dwidevinecdma'
                'dapter%7Cpepperflashplayer%7Cinternal%2Dremoting%2Dviewer%7Cinternal%2Dnacl%2Dplugin%7Cpdf%7Cdefa'
                'ult%20browser%7Cflash%20player%7Cgoogletalkbrowserplugin%7Cjavaappletplugin%7Clogmein%7Co1dbrowse'
                'rplugin%26pm%5Ffpan%3DNetscape%26pm%5Ffpacn%3DMozilla%26pm%5Ffpol%3Dtrue%26pm%5Ffposp%3D%26pm%5Ff'
                'pup%3D%26pm%5Ffpsaw%3D1680%26pm%5Ffpspd%3D24%26pm%5Ffpsbd%3D%26pm%5Ffpsdx%3D%26pm%5Ffpsdy%3D%26pm'
                '%5Ffpslx%3D%26pm%5Ffpsly%3D%26pm%5Ffpsfse%3D%26pm%5Ffpsui%3D'),
            'pageToken': pageToken
        }
        response = session.post(url, params=params, data=data)

        # Check for the "Update your contact info" prompt
        html = lxml.html.fromstring(response.text)
        buttons = html.xpath('//form//span[contains(concat(" ",normalize-space(@class)," ")," bluebutton ")]/a')
        for button in buttons:
            if button.text.strip() == 'Remind Me Later':
                pageToken = html.xpath("//input[@name='pageToken']")[0].get('value')
                url = 'https://secure.capitalone360.com/myaccount/banking/boarding_pass.vm'
                data = {
                    'eventName': 'remind',
                    'pageToken': pageToken
                }
                response = session.post(url, data=data)
                break

        # Gather account links
        account_data_list = []
        html = lxml.html.fromstring(response.text)
        for account_row in html.xpath('//tbody[@class="m_account_summary_table"]/tr'):
            link = 'https://secure.capitalone360.com/myaccount/banking/' + account_row.xpath('td[1]/a')[0].attrib['href']
            number = account_row.xpath('td[2]/a')[0].text.strip()
            balance = account_row.xpath('td[3]/a')[0].text.strip()
            account_data_list.append({'link': link, 'number': number, 'balance': balance})

        # Gather transactions
        statements = []
        for account_data in account_data_list:
            response = session.get(account_data['link'])
            html = lxml.html.fromstring(response.text)
            rows = html.xpath('//tbody[@id="transactionstable"]/tr')
            transactions = []

            expand_row_next = False
            for row in rows:
                if expand_row_next:
                    expand_row_next = False
                    continue

                # When 'expandRow' is present, the next tr element is used for additional
                # detail, not for a transaction
                if 'expandRow' in row.attrib['class']:
                    expand_row_next = True

                tx = Transaction()
                if 'onclick' in row.attrib:
                    tx.tid = re.search('historySequenceNumber=(\d+)', row.attrib['onclick']).groups()[0]
                tds = row.xpath('td')
                date_parts = [span.text for span in tds[0].xpath('.//span') if span.text]
                tx.date = dateutil.parser.parse(' '.join(date_parts))
                tx.description = ' '.join(tds[2].text_content().split() + tds[3].text_content().split())

                # Interest rate changes don't have an amount, but they can be ignored
                withdrawal = tds[4].text_content().strip()
                deposit = tds[5].text_content().strip()
                if deposit == '' and withdrawal == '':
                    continue
                if len(withdrawal) > len(deposit):
                    tx.amount = withdrawal
                    tx.amount = -tx.amount
                else:
                    tx.amount = deposit

                transactions.append(tx)

            account = Account(number=account_data['number'], balance=account_data['balance'])
            statements.append(Statement(account=account, transactions=transactions))

        # Log out
        session.get('https://secure.capitalone360.com/myaccount/banking/logout.vm')

        return statements

    @classmethod
    def _fetch_ally(cls, username, password, questions):
        session = requests.Session()

        # Get the XSRF token
        response = session.post('https://securebanking.ally.com/IDPProxy/userstatusenquiry/olbWeb')
        token = response.headers['csrfchallengetoken']
        session.headers.update({'CSRFChallengeToken': token})

        # Log in
        url = 'https://securebanking.ally.com/IDPProxy/executor/session'
        headers = {
            'ApplicationId': 'ALLYUSBOLB',
            'ApplicationName': 'AOB',
            'ApplicationVersion': '1.0',
        }
        data = {
            'channelType': 'OLB',
            'passwordPvtBlock': password,
            'rememberMeFlag': 'false',
            'userNamePvtEncrypt': username
        }
        response = session.post(url, headers=headers, data=data)

        # Complete log in
        response = session.get('https://securebanking.ally.com/IDPProxy/executor/session/consents')

        # Request accounts
        response = session.get('https://securebanking.ally.com/IDPProxy/executor/accounts')

        # Parse accounts xml
        statements = []
        account_ids = []
        response_fragment = re.search('<?xml [^>]*>(.*)', response.text).groups()[0]
        html = lxml.html.fromstring(response_fragment)
        for balance_element in html.xpath('//accountsummary/currentbalancepvtencrypt'):
            account = Account(org='ally', username=username)
            account.number = balance_element.getparent().xpath('accountnumberpvtencrypt')[0].text
            account.balance = balance_element.text
            account_ids.append(balance_element.getparent().xpath('accountid')[0].text)
            statements.append(Statement(account=account))

        for index, statement in enumerate(statements):
            # Request transactions
            url = 'https://securebanking.ally.com/IDPProxy/executor/accounts/{}/transactions'
            start = datetime.datetime.now() - datetime.timedelta(days=30)
            params = {'fromDate': start.strftime('%Y-%m-%d')}
            response = session.get(url.format(account_ids[index]), params=params)

            # Parse transactions xml
            response_fragment = re.search('<?xml [^>]*>(.*)', response.text).groups()[0]
            html = lxml.html.fromstring(response_fragment)
            for tx_element in html.xpath('//transaction'):
                tx = Transaction()
                tx.tid = tx_element.xpath('transactionid')[0].text
                tx.date = tx_element.xpath('transactionpostingdate')[0].text
                tx.amount = tx_element.xpath('transactionamountpvtencrypt')[0].text
                tx.description = tx_element.xpath('transactiondescription')[0].text
                statement.transactions.append(tx)

        # Log out
        session.delete('https://securebanking.ally.com/IDPProxy/executor/session')

        return statements

    @classmethod
    def _fetch_barclay(cls, username, password, questions):
        session = requests.Session()

        # Get XSRF token
        response = session.get('https://www.barclaycardus.com/servicing/')
        html = lxml.html.fromstring(response.text)
        token = html.xpath("//input[@name='__fp']")[0].get('value')

        # Submit username
        url = 'https://www.barclaycardus.com/servicing/login'
        data = {
            '__fp': token,
            'login': 'Log in',
            'username': username
        }
        response = session.post(url, data=data)
        html = lxml.html.fromstring(response.text)
        encrypted_username = html.xpath("//input[@name='username']")[0].get('value')

        # Submit password
        url = 'https://www.barclaycardus.com/servicing/login'
        data = {
            'username': encrypted_username,
            '__fp': token,
            'submitPassword': 'Log in',
            'password': password
        }
        response = session.post(url, data=data)

        # Find all account numbers
        account_numbers = []
        html = lxml.html.fromstring(response.text)
        link_elements = lxml.html.fromstring(response.text).xpath('//a')
        for link_element in link_elements:
            href = link_element.get('href')
            if href:
                matches = re.search(r'^SwitchAccount\.action\?accountId=([\d]+)$', href)
                if matches and matches.group(1) not in account_numbers:
                    account_numbers.append(matches.group(1))

        # Calculate start and end date of statement to download
        now = datetime.datetime.now()
        start_date = (now + datetime.timedelta(-30)).strftime('%m/%d/%y')
        end_date = now.strftime('%m/%d/%y')

        statements = []
        for account_number in account_numbers:
            # Switch to an account
            url = 'https://www.barclaycardus.com/servicing/SwitchAccount.action?accountId={}'
            response = session.get(url.format(account_number))

            # Download OFX statement
            url = 'https://www.barclaycardus.com/servicing/downloadTransactions'
            data = {
                'exportTransactions': 'Download',
                'format': 'QUICKEN',
                'fromDate': start_date,
                'toDate': end_date
            }
            response = session.post(url, data=data)

            # Parse OFX statement
            statement = OfxParser.parse(ofx_string=response.text, org='barclay', username=username)
            statements.append(statement)

        # Log out
        session.get('https://www.barclaycardus.com/servicing/logout')

        return statements

    @classmethod
    def _fetch_usbank(cls, username, password, questions):
        session = requests.Session()

        # Submit username
        url = 'https://onlinebanking.usbank.com/Auth/Login/Login'
        data = {
            'USERID': username
        }
        response = session.post(url, data=data)

        # Find security question answer
        html = lxml.html.fromstring(response.text)
        question = html.xpath("//input[@name='StepUpShieldQuestion.QuetionText']")[0].get('value')
        answer = questions[question]

        # Submit security question answer
        url = 'https://onlinebanking.usbank.com/Auth/Login/StepUpCheck'
        data = {
            'StepUpShieldQuestion.Answer': answer,
            'StepUpShieldQuestion.QuetionText': question
        }
        response = session.post(url, data=data)

        # Submit password
        url = 'https://onlinebanking.usbank.com/access/oblix/apps/webgate/bin/webgate.dll?/Auth/Signon/Signon'
        data = {
            'password': password,
            'userid': username
        }
        response = session.post(url, data=data)

        # Find session token
        token = re.search(r'af\(([^\)]+)\)', response.url).group(1)

        # Get list of accounts
        url = 'https://onlinebanking.usbank.com/USB/af({})/AccountDashboard/GetDownloadAccounts'.format(token)
        headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }
        response = session.post(url, headers=headers)

        statements = []
        now = datetime.datetime.now()
        for account_json in json.loads(response.text):

            # Refresh transaction history
            url = 'https://onlinebanking.usbank.com/USB/af({})/AccountDashboard/RefreshTransactionHistory'
            headers = {
                'Content-Type': 'application/json; charset=UTF-8'
            }
            data = json.dumps({"AccountIndex": account_json['Index']})
            response = session.post(url.format(token), headers=headers, data=data)

            # Download OFX statement
            params = {
                'token': token,
                'index': account_json['Index'],
                'from': (now + datetime.timedelta(days=-30)).strftime('%m/%d/%Y'),
                'to': now.strftime('%m/%d/%Y')
            }
            url = 'https://onlinebanking.usbank.com/USB/af({token})/AccountDashboard/Download.aspx?index={index}&from={from}&to={to}&type=qfx1'
            response = session.get(url.format(**params))

            # Parse OFX statement, or construct an empty account if there is no statement
            if len(response.text) > 0:
                statement = OfxParser.parse(ofx_string=response.text, org='usbank', username=username)
            else:
                number = account_json['AccountNumber'][-16:]
                balance = account_json['CurrentBalance']
                account = Account(org='usbank', username=username, number=number, balance=balance)
                statement = Statement(account=account, transactions=[])
            statements.append(statement)

        # Log out
        session.get('https://onlinebanking.usbank.com/Auth/LogoutConfirmation')

        return statements

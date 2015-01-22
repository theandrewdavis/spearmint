import lxml.html
import requests

from . import OfxFetcher

def fetch(login):
    methods = {
        'citi': _fetch_citi,
        'amex': _fetch_amex,
        'chase': _fetch_chase,
        'citi': _fetch_citi,
        'citibusiness': _fetch_citibusiness,
        'schwab': _fetch_schwab,
        'capitalone360': _fetch_capitalone360
    }
    if login.bank not in methods:
        raise 'Not implemented'
    return methods[login.bank](login)

def _fetch_citi(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='Citigroup',
        fid='24909',
        url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

def _fetch_citibusiness(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='Citigroup',
        fid='26389',
        url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

def _fetch_amex(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='AMEX',
        fid='3101',
        url='https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload')

def _fetch_chase(login):
    statements = OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='B1',
        fid='10898',
        url='https://ofx.chase.com')
    unique_statements = []
    usernames = []
    for statement in statements:
        if statement.account.username not in usernames:
            unique_statements.append(statement)
            usernames.append(statement.account.username)
    return unique_statements

def _fetch_schwab(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='101',
        fid='ISC',
        url='https://ofx.schwab.com/bankcgi_dev/ofx_server')

def _scrape_capitalone360(login):
    session = requests.Session()

    # Submit username
    url = 'https://secure.capitalone360.com/myaccount/banking/login.vm'
    response = session.post(url, data={'publicUserId': login.username})

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
        'currentPassword_TLNPI': login.password,
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
        print('{} {} {}'.format(link, number, balance))

    # Gather transactions
    statements = []
    for account_data in account_data_list:
        response = session.get(account_data['link'])
        html = lxml.html.fromstring(response.text)
        rows = html.xpath('//tbody[@id="transactionstable"]/tr')
        transactions = []
        i = 0
        while i < len(rows):
            row = rows[i]
            tds = row.xpath('td')
            date_parts = [span.text for span in tds[0].xpath('.//span') if span.text]
            date = dateutil.parser.parse(' '.join(date_parts))
            description = ' '.join(tds[2].text_content().split() + tds[3].text_content().split())
            withdrawal = tds[4].text_content().strip()
            deposit = tds[5].text_content().strip()
            amount = withdrawal if len(withdrawal) > len(deposit) else deposit
            transactions.append(Transaction(date=date, amount=amount, description=description))

            # When 'expandRow' is present, the next tr element is used for additional
            # detail, not for a transaction
            i += 1
            if 'expandRow' in row.attrib['class']:
                i += 1

        account = Account(number=account_data['number'], balance=account_data['balance'])
        statements.append(Statement(account=account, transactions=transactions))

    # Log out
    session.get('https://secure.capitalone360.com/myaccount/banking/logout.vm')

    return statements

def _match_capitalone360_tx(ofx_tx, scrape_tx):
    if ofx_tx.date != scrape_tx.date or ofx_tx.amount != scrape_tx.amount:
        return False
    return ofx_tx.description in scrape_tx.description

def _merge_capitalone360(ofx_statements, scrape_statements):
    for ofx_statement in ofx_statements:
        # Match statements by account number
        scrape_numbers = [statement.account.number for statement in scrape_statements]
        scrape_statement = scrape_statements[scrape_numbers.index(ofx_statement.account.number)]

        for ofx_tx in ofx_statement.transactions:
            # Match transactions by date and amount
            matches = filter(lambda scrape_tx: _match_capitalone360_tx(ofx_tx, scrape_tx), scrape_statement.transactions)

            # Ignore ambiguous transactions
            if len(matches) == 1:
                print('Added description "{}"'.format(matches[0].description))
                ofx_tx.description = matches[0].description
            else:
                print('Ambiguous: {} matches'.format(len(matches)))

def _fetch_capitalone360(login):
    ofx_statements = OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='ING DIRECT',
        fid='031176110',
        url='https://ofx.capitalone360.com/OFX/ofx.html')
    scrape_statements = _scrape_capitalone360(login)
    _merge_capitalone360(ofx_statements, scrape_statements)
    return ofx_statements

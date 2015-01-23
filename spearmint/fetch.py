from . import OfxFetcher, ScrapeFetcher

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

def _merge_capitalone360(ofx_statements, scrape_statements):
    for ofx_statement in ofx_statements:
        # Match statements by account number
        scrape_numbers = [statement.account.number for statement in scrape_statements]
        scrape_statement = scrape_statements[scrape_numbers.index(ofx_statement.account.number)]

        # Match transactions by date and amount
        for ofx_tx in ofx_statement.transactions:
            matches = []
            for scrape_tx in scrape_statement.transactions:
                if ofx_tx.amount != scrape_tx.amount:
                    continue
                if scrape_tx.date.date() < ofx_tx.date.date() - datetime.timedelta(days=1):
                    continue
                if scrape_tx.date.date() > ofx_tx.date.date():
                    continue
                matches.append(scrape_tx)

            if len(matches) == 0:
                continue

            # If there's only one match or all the matches have the same description,
            # use the description from the scraped transaction
            if all([match.description == matches[0].description for match in matches]):
                ofx_tx.description = matches[0].description

def _fetch_capitalone360(login):
    ofx_statements = OfxFetcher.fetch(
        username=login.username,
        password=login.access_code,
        org='ING DIRECT',
        fid='031176110',
        url='https://ofx.capitalone360.com/OFX/ofx.html')
    scrape_statements = ScrapeFetcher.fetch(
        bank=login.bank,
        username=login.username,
        password=login.password)
    _merge_capitalone360(ofx_statements, scrape_statements)
    return ofx_statements

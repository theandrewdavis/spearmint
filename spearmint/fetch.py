import datetime

from . import OfxFetcher, ScrapeFetcher, Login

def fetch(login, interactive=False):
    return Fetcher.fetch(login, interactive)

class Fetcher(object):
    @classmethod
    def _bank_info(cls, bank):
        banks = {
            'citi':             {'method': cls._fetch_citi,             'extra': []                 },
            'amex':             {'method': cls._fetch_amex,             'extra': []                 },
            'chase':            {'method': cls._fetch_chase,            'extra': []                 },
            'citi':             {'method': cls._fetch_citi,             'extra': []                 },
            'citibusiness':     {'method': cls._fetch_citibusiness,     'extra': []                 },
            'schwab':           {'method': cls._fetch_schwab,           'extra': []                 },
            'capitalone360':    {'method': cls._fetch_capitalone360,    'extra': ['access_code']    },
            'ally':             {'method': cls._fetch_ally,             'extra': []                 },
            'barclay':          {'method': cls._fetch_barclay,          'extra': []                 },
            'usbank':           {'method': cls._fetch_usbank,           'extra': ['questions']      }
        }
        if bank not in banks:
            raise Exception('Bank "{}" not implemented'.format(bank))
        return (banks[bank]['method'], banks[bank]['extra'])

    @classmethod
    def fetch(cls, login, interactive=False):
        method, extra = cls._bank_info(login.bank)
        for arg in extra:
            if not login.extra or arg not in login.extra.keys():
                raise Exception('Missing argument "{}"'.format(arg))
        return method(login, interactive)

    @classmethod
    def extra(cls, bank):
        return cls._bank_info(login.bank)[1]

    @classmethod
    def _fetch_citi(cls, login, interactive):
        return OfxFetcher.fetch(
            username=login.username,
            password=login.password,
            org='Citigroup',
            fid='24909',
            url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

    @classmethod
    def _fetch_citibusiness(cls, login, interactive):
        return OfxFetcher.fetch(
            username=login.username,
            password=login.password,
            org='Citigroup',
            fid='26389',
            url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

    @classmethod
    def _fetch_amex(cls, login, interactive):
        return OfxFetcher.fetch(
            username=login.username,
            password=login.password,
            org='AMEX',
            fid='3101',
            url='https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload')

    @classmethod
    def _fetch_chase(cls, login, interactive):
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

    @classmethod
    def _fetch_schwab(cls, login, interactive):
        return OfxFetcher.fetch(
            username=login.username,
            password=login.password,
            org='101',
            fid='ISC',
            url='https://ofx.schwab.com/bankcgi_dev/ofx_server')

    @classmethod
    def _merge_capitalone360(cls, ofx_statements, scrape_statements):
        for ofx_statement in ofx_statements:
            # Match statements by account number
            scrape_numbers = [statement.account.number for statement in scrape_statements]
            scrape_statement = scrape_statements[scrape_numbers.index(ofx_statement.account.number)]

            # Match transactions by tid
            ofx_tx_remaining = ofx_statement.transactions[:]
            for ofx_tx in ofx_statement.transactions:
                matches = [tx for tx in scrape_statement.transactions if tx.tid == ofx_tx.tid]
                if len(matches) == 1:
                    ofx_tx.description = matches[0].description
                    ofx_tx_remaining.remove(ofx_tx)
                    scrape_statement.transactions.remove(matches[0])

            # Match remaining transactions by date and amount
            for ofx_tx in ofx_tx_remaining:
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

                # If two scraped transactions have no tids, different descriptions, and the same
                # date and amount, matching fails. This could be improved by comparing the
                # descriptions of the ofx and scrape transactions.

    @classmethod
    def _fetch_capitalone360(cls, login, interactive):
        ofx_statements = OfxFetcher.fetch(
            username=login.username,
            password=login.extra['access_code'],
            org='ING DIRECT',
            fid='031176110',
            url='https://ofx.capitalone360.com/OFX/ofx.html')
        scrape_statements = ScrapeFetcher.fetch(
            bank=login.bank,
            username=login.username,
            password=login.password,
            interactive=interactive)
        cls._merge_capitalone360(ofx_statements, scrape_statements)
        return ofx_statements

    @classmethod
    def _fetch_ally(cls, login, interactive):
        return ScrapeFetcher.fetch(
            bank=login.bank,
            username=login.username,
            password=login.password,
            interactive=interactive)

    @classmethod
    def _fetch_barclay(cls, login, interactive):
        return ScrapeFetcher.fetch(
            bank=login.bank,
            username=login.username,
            password=login.password,
            interactive=interactive)

    @classmethod
    def _fetch_usbank(cls, login, interactive):
        return ScrapeFetcher.fetch(
            bank=login.bank,
            username=login.username,
            password=login.password,
            questions=login.extra['questions'],
            interactive=interactive)

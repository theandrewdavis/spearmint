from . import OfxFetcher

# Fetch transactions from web
def fetch(login):
    if login.bank == 'citi':
        return _fetch_citi(login)
    else:
        raise 'Not implemented'

def _fetch_citi(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='Citigroup',
        fid='24909',
        url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

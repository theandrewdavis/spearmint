from . import OfxFetcher

# Fetch transactions from web
def fetch(bank=None, username=None, password=None):
    if bank == 'citi':
        return _fetch_citi(username, password)
    else:
        raise 'Not implemented'

def _fetch_citi(username, password):
    return OfxFetcher.fetch(
        username=username,
        password=password,
        org='Citigroup',
        fid='24909',
        url='https://www.accountonline.com/cards/svc/CitiOfxManager.do')

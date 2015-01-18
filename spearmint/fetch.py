from . import OfxFetcher

def fetch(login):
    methods = {
        'citi': _fetch_citi,
        'amex': _fetch_amex
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

def _fetch_amex(login):
    return OfxFetcher.fetch(
        username=login.username,
        password=login.password,
        org='AMEX',
        fid='3101',
        url='https://online.americanexpress.com/myca/ofxdl/desktop/desktopDownload.do?request_type=nl_ofxdownload')

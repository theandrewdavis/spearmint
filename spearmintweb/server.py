import bottle
import logging
import spearmint
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from . import Database, Login

class Server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = bottle.Bottle()
        self._route()

    def run(self):
        ScheduledUpdater.run()
        self.app.run(host=self.host, port=self.port)

    def _route(self):
        self.app.route('/', method='GET', callback=self._index)
        self.app.route('/<path:path>', method='GET', callback=self._static)
        self.app.route('/api/summary', method='GET', callback=self._api_summary)

    def _index(self):
        return bottle.static_file('index.html', root='static')

    def _static(self, path):
        return bottle.static_file(path, root='static')

    def _api_summary(self):
        accounts = [account.as_dict() for account in Database.all_accounts()]
        transactions = [tx.as_dict() for tx in Database.all_transactions()]
        return {'accounts': accounts, 'transactions': transactions}

class ScheduledUpdater(object):
    @classmethod
    def merge(cls):
        for login in Login.load('banks.yaml'):
            statements = spearmint.fetch(login.info)
            Database.merge_statements(statements)

    @classmethod
    def run(cls):
        logging.basicConfig()
        scheduler = BackgroundScheduler()
        scheduler.add_job(cls.merge, 'interval', minutes=10)
        scheduler.start()

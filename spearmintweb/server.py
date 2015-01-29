import bottle
import logging
import spearmint
import yaml
from apscheduler.schedulers.background import BackgroundScheduler

from . import Account, Transaction, Updater

class Server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = bottle.Bottle()
        self._route()

    def run(self):
        Updater.run_periodically()
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
        return {'accounts': Account.all(), 'transactions': Transaction.all()}

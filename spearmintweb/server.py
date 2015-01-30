import bottle
import os
import spearmint

from . import Account, Transaction, Updater


class Server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = bottle.Bottle()
        self._route()
        self._static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

    def run(self):
        Updater.run_periodically()
        self.app.run(host=self.host, port=self.port)

    def _route(self):
        self.app.route('/', method='GET', callback=self._index)
        self.app.route('/<path:path>', method='GET', callback=self._static)
        self.app.route('/api/summary', method='GET', callback=self._api_summary)

    def _index(self):
        return bottle.static_file('index.html', root=self._static_dir)

    def _static(self, path):
        return bottle.static_file(path, root=self._static_dir)

    def _api_summary(self):
        return {'accounts': Account.all(), 'transactions': Transaction.all()}

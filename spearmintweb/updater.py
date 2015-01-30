import logging
import spearmint
import yaml

from apscheduler.schedulers.background import BackgroundScheduler
from . import Account, Transaction

class Updater(object):
    @classmethod
    def merge_bank_data(cls):
        with open('config.yaml', 'r') as file:
            config = yaml.load(file.read())
            logins = [spearmint.Login(**info) for info in config['logins']]
            for login in logins:
                statements = spearmint.fetch(login)
                for statement in statements:
                    account = statement.account
                    Account.upsert_bank_data(account.org, account.username, account.number, account.balance)
                    account_id = Account.find_aid(account.org, account.username, account.number)
                    for tx in statement.transactions:
                        Transaction.upsert_bank_data(account_id, tx.tid, tx.date, tx.amount, tx.description)

    @classmethod
    def run_periodically(cls):
        logging.basicConfig()
        scheduler = BackgroundScheduler()
        scheduler.add_job(cls.merge_bank_data, 'interval', minutes=10)
        scheduler.start()

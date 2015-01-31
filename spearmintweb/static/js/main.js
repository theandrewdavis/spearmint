$(function () {
    var accountTemplate = _.template($('#account-template')[0].innerHTML);
    var transactionTemplate = _.template($('#transaction-template')[0].innerHTML);
    $.getJSON('/api/summary', function (data) {
        // Format account balances table
        var accountData = _.map(data['accounts'], function (account) {
            if (!account['name']) {
                account['name'] = account['org'] + ':' + account['username'] + ':' + account['number'];
            }
            return account;
        });
        var tableHTML = _.map(accountData, accountTemplate).join("");
        $('.accounts tbody')[0].innerHTML = tableHTML;

        // Format transactions table
        var accountNames = _.object(_.map(accountData, function (account) {
            return [account['aid'], account['name']];
        }));
        var transactionData = _.map(data['transactions'], function (tx) {
            if (tx['amount'] >= 0) {
                tx['from_account'] = '';
                tx['to_account'] = accountNames[tx['aid']];
            } else {
                tx['to_account'] = '';
                tx['from_account'] = accountNames[tx['aid']];
            }
            tx['amount'] = Math.abs(tx['amount']);
            return tx;
        });
        tableHTML = _.map(transactionData, transactionTemplate).join("");
        $('.transactions tbody')[0].innerHTML = tableHTML;
    })
});

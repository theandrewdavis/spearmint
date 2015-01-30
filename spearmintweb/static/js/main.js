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
        tableHTML = _.map(data['transactions'], transactionTemplate).join("");
        $('.transactions tbody')[0].innerHTML = tableHTML;
    })
})
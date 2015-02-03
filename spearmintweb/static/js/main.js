$(function () {

    var AccountTable = function (json) {
        this.json = json;
        this.template = _.template($('#account-template')[0].innerHTML);
        this.names = this.prepareNames(json);
    };

    AccountTable.prototype.layout = function (json) {
        var data = _.map(this.json, this.rowData, this);
        var html = _.map(data, this.template).join("");
        $('.accounts tbody')[0].innerHTML = html;
    };

    AccountTable.prototype.rowData = function (json) {
        var formatted = {};
        formatted['aid'] = json['aid'];
        formatted['name'] = this.accountName(json['aid']);
        formatted['balance'] = (Math.abs(parseInt(json['balance'])) / 100).toFixed(2);
        return formatted;
    };

    AccountTable.prototype.prepareNames = function(json) {
        return _.object(_.map(json, function (account_json) {
            var name = account_json['name'];
            if (!name) {
                name = account_json['org'] + ':' + account_json['username'] + ':' + account_json['number'];
            }
            return [account_json['aid'], name];
        }));
    };

    AccountTable.prototype.accountName = function (aid) {
        return this.names[aid];
    };

    var TransactionTable = function (json, accountTable) {
        this.json = json;
        this.accountTable = accountTable;
        this.template = _.template($('#transaction-template')[0].innerHTML);
    };

    TransactionTable.prototype.layout = function () {
        var data = _.map(this.json, this.rowData, this);
        var html = _.map(data, this.template).join("");
        $('.transactions tbody')[0].innerHTML = html;
    };

    TransactionTable.prototype.rowData = function (json) {
        var formatted = {};
        var amount = parseInt(json['amount']);
        var accountName = this.accountTable.accountName(json['aid']);
        formatted['date'] = this.formatDate(json['date']);
        formatted['amount'] = (Math.abs(amount) / 100).toFixed(2);
        formatted['from_account'] = (amount >= 0) ? accountName : '';
        formatted['to_account'] = (amount >= 0) ? '' : accountName;
        formatted['description'] = json['description'];
        return formatted;
    };

    TransactionTable.prototype.formatDate = function (iso8601) {
        var parts = iso8601.split('-');
        var date = new Date(parts[0], parseInt(parts[1]) - 1, parts[2]);
        return date.toLocaleDateString('en-US');
    };

    $.getJSON('/api/summary', function (json) {
        var accountTable = new AccountTable(json['accounts']);
        var txTable = new TransactionTable(json['transactions'], accountTable);
        accountTable.layout();
        txTable.layout();
    });
});

$(function () {
    var accountTemplate = _.template($('#account-template')[0].innerHTML);
    var transactionTemplate = _.template($('#transaction-template')[0].innerHTML);
    $.getJSON('/api/summary', function (data) {
        var tableHTML = _.map(data['accounts'], accountTemplate).join("");
        $('.accounts tbody')[0].innerHTML = tableHTML;
        tableHTML = _.map(data['transactions'], transactionTemplate).join("");
        $('.transactions tbody')[0].innerHTML = tableHTML;
    })
})
$(function () {
    var template = _.template($('#transaction-template')[0].innerHTML);
    $.getJSON('/api/transactions', function (data) {
        var tableHTML = _.map(data['transactions'], template).join("");
        $('.transactions tbody')[0].innerHTML = tableHTML;
    })
})
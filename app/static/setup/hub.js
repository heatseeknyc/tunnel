$(function() {
    $('#hourly').click(function() {
	$.ajax({method: 'PATCH', data: {hourly: true}});
    });
});

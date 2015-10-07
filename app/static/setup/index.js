$(function() {
    $('#go').click(function() {
	location = '/' + $('#xbee_id').val().toLowerCase().replace('o', '0');
    });
});

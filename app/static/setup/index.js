$(function() {
    $('#form').submit(function() {
	location = '/' + $('#xbee_id').val().toLowerCase().replace('o', '0');
    });
});

$(function() {
    $('#go').click(function() {
	location = HUBS_URL + '/' + $('#xbee_id').val();
    });
});

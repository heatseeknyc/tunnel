$(function() {
    $('#form').submit(function(event) {
        event.preventDefault();
        location = '/' + $('#xbee_id').val().toLowerCase().replace('o', '0');
    });
});

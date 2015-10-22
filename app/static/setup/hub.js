$(function() {

  $('#hourly').click(function() {
    $.ajax(RELAY_HUB_URL, {method: 'PATCH', data: {hourly: true}});
  });

});

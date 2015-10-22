$(function() {

  $('#hourly').click(function() {
    $.ajax(HUB_URL, {method: 'PATCH', data: {hourly: true}});
  });

});

$(function() {

  function refresh() {
    $.when($.get(HUB_PARTIAL_URL), $.get(CELLS_PARTIAL_URL))
      .done(function(hub_partial, cells_partial) {
        console.log(hub_partial);
        console.log(cells_partial);

        $('#hub-data').html(hub_partial[0]);
        $('#cells-data').html(cells_partial[0]);
        refreshSoon();
      });
  }

  function refreshSoon() {
    setTimeout(refresh, 5000);
  }

  $('#hourly').click(function() {
    $.ajax(HUB_URL, {method: 'PATCH', data: {hourly: true}});
  });

  refreshSoon();

});

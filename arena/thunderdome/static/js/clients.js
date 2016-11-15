var iter, params, scroll_meister, stopper;

$(document).ready(function() {
  var table = $("#clients").DataTable({
    lengthChange: false,
    deferRender: true,
    scrollY: 600,
    scrollCollapse: true,
    dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
      "<'row'<'col-sm-12'tr>>",
    ajax: "api/get_clients",
    columns: [
      { data: "rank"},
      { data: "client_name"},
      { data: "embargoed?"},
      { data: "embargo_reason"},
      { data: "missing?"},
      { data: "last_game_played"},
      { data: "current_version"},
      { data: "language"},
    ],
    drawCallback: function(settings) {
      $('.dataTables_scrollBody').addClass('hidden_scrollbar');
    }
  });
                  
  setInterval(function() {
    table.ajax.reload(null, false);
  }, 20000);
});




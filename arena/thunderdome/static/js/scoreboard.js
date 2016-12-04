var iter, params, scroll_meister, stopper;

$(document).ready(function() {
  var table = $("#scoreboard").DataTable({
    searching: false,
    ordering: false,
    lengthChange: false,
    deferRender: true,
    scrollY: 600,
    scrollCollapse: true,
    scroller: true,
    dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
      "<'row'<'col-sm-12'tr>>",
    ajax: "api/get_scores",
    columns: [
      { data: "rank"},
      { data: "name"},
      { data: "score"},
      { data: "sum_of_opps_score"},
      { data: "sum_of_opps_rat"},
      { data: "num_black"},
      { data: "language"}
    ],
    drawCallback: function(settings) {
      $('.dataTables_scrollBody').addClass('hidden_scrollbar');
    }
  });
                  
  setInterval(function() {
    table.ajax.reload(null, false);
  }, 10000);

  function auto_scroll(iter) {
    var next = iter.next();
    if(next.done) return function() {};
    console.log("next row: ", next.value);
    return function(){
      if(next.value == 0)
	setTimeout(auto_scroll(iter), 6000);
      else
        setTimeout(auto_scroll(iter), 1250);
      table.row(next.value).scrollTo();
    };
  };

  function* iter_mod(start, mod) {
    var i = start, value = start;
    while(true) {
      i = Math.floor(++i % mod);
      value = yield i;
    }
  };

  table.on('xhr.dt', function(e,settings,json,xhr) {
    params = {start: 0, end: json["data"].length-13};
    gen_maker = iter_mod;
    stopper = iter_mod(params.start, params.end);
    scroll_meister = setTimeout(auto_scroll(stopper), 4000);
    table.off('xhr.dt');
  });
});




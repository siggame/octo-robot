var iter, params, scroll_meister, stopper;

$(document).ready(function() {
  var table = $("#scoreboard").DataTable({
    lengthChange: false,
    deferRender: true,
    scrollY: 600,
    scrollCollapse: true,
    scroller: true,
    dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
      "<'row'<'col-sm-12'tr>>",
    ajax: "api/get_mmai_scores",
    columns: [
      { data: "rank"},
      { data: "name"},
      { data: "rating"}
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
    table.row(next.value).scrollTo();
    return function(){
      if(next.value == 0)
        setTimeout(auto_scroll(iter), 1500);
      if(next.value == 1)
        setTimeout(auto_scroll(iter), 3000);
      else
        setTimeout(auto_scroll(iter), 2500);
    };
  };

  function* iter_mod(start, mod) {
    var i = start, value = start;
    while(true) {
      i = ++i % mod;
      value = yield i;
    }
  };

  table.on('xhr.dt', function(e,settings,json,xhr) {
    params = {start: 0, end: json["data"].length-6};
    gen_maker = iter_mod;
    stopper = iter_mod(params.start, params.end);
    scroll_meister = setTimeout(auto_scroll(stopper), 3000);
    table.off('xhr.dt');
  });
});

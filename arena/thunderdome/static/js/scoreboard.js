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
    ajax: "api/get_scores",
    columns: [
      { data: "rank"},
      { data: "name"},
      { data: "score"},
      { data: "sum_of_opps_score"},
      { data: "sum_of_opps_rat"},
      { data: "num_black"}
    ],
  });
                  
  setInterval(function() {
    table.ajax.reload(null, false);
  }, 10000);

  function auto_scroll(iter) {
    var next = iter.next();
    if(next.done) return function() {};
    table.row(next.value).scrollTo();
    return function(){
      setTimeout(auto_scroll(iter), 750);
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
    scroll_meister = auto_scroll(stopper)();
    table.off('xhr.dt');
  });
});




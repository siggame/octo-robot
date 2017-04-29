var iter, params, scroll_meister, stopper;

function getParameterByName(name, url) {
  if (!url) url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)");
  var results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}

$(document).ready(function() {
  var table = $("#scoreboard").DataTable({
    searching: false,
    ordering: false,
    lengthChange: false,
    deferRender: true,
    scrollY: 600,
    scrollCollapse: true,
    scroller: getParameterByName("autoscroll") !== null,
    dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
      "<'row'<'col-sm-12'tr>>",
    ajax: "api/get_mmai_scores",
    columns: [
      { data: "rank"},
      { data: "name"},
      { data: "rating"},
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
      else if(next.value == 1)
        setTimeout(auto_scroll(iter), 2500);
      else
        setTimeout(auto_scroll(iter), 2250);
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
    //scroll_meister = setTimeout(auto_scroll(stopper), 3000);
    table.off('xhr.dt');
  });
});

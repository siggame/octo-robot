$(document).ready(function() {
  var Scores = {
    table: {},
    init: function() {
      this.table = $("#scoreboard").DataTable({
        "ajax": "api/get_scores",
        "columns": [
          { data: "rank"},
          { data: "name"},
          { data: "score"},
          { data: "sum_of_opps_score"},
          { data: "sum_of_opps_rat"},
          { data: "num_black"}
        ]
      });
    },
    
    update_scores: function() {
      var self = this;
      setInterval(function() {
        self.table.ajax.reload(null, false);
      }, 10000);
    }
  };

  Scores.init();
  Scores.update_scores();
});


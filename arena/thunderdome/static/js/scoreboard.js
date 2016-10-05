$(function() {
  var Scores = {
    init: function() {
      $("#scoreboard").DataTable({
        "ajax": "../api/get_scores",
      });
    },
    
    update_scores: function() {
      
    }
  }
}


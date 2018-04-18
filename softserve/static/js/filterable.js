function doSearch() {
  var q = document.getElementById("q");
  var v = q.value.toLowerCase();
  var rows = document.getElementsByTagName("tr");
  var on = 0;
  for ( var i = 0; i < rows.length; i++ ) {
    var fullname = rows[i].getElementsByTagName("td");
    fullname = fullname[0].innerHTML.toLowerCase();
    if ( fullname ) {
        if ( v.length == 0 || (v.length < 3 && fullname.indexOf(v) == 0) || (v.length >= 3 && fullname.indexOf(v) > -1 ) ) {
        rows[i].style.display = "";
        on++;
      } else {
        rows[i].style.display = "none";
      }
    }
  }
  var n = document.getElementById("noresults");
  if ( on == 0 && n ) {
    n.style.display = "";
    document.getElementById("qt").innerHTML = q.value;
  } else {
    n.style.display = "none";
  }
}

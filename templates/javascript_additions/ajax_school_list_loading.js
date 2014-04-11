
var base_url = window.location.protocol + "//" + window.location.host;

// Load school list when page is first accessed.
$(document).ready(function(){
    loadSchoolList();
});

// Loads school list tab and makes the list a dataTable (search functionality, etc.)
function loadSchoolList() {
    $('#school_list_tab').load(base_url + '/school/list/', function() {
        $('#school_list').dataTable( {
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': [ -2, -1 ] }
            ]
        });
    });
};

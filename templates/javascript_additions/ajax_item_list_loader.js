
var base_url = window.location.protocol + "//" + window.location.host;

// Loads school list tab and makes the list a dataTable (search functionality, etc.)
function load_item_list(item_tab_id, item_list_url, n_headings_to_exclude, load_javascript) {
    var exclude_headings = new Array();
    for (var back_index = 0; back_index < n_headings_to_exclude; back_index++)
        exclude_headings[back_index] = -n_headings_to_exclude + back_index;
    $('#' + item_tab_id).load(base_url + item_list_url + (load_javascript ? "" : " #non_js_container"), function() {
        $('#item_list_table').dataTable( {
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': exclude_headings }
            ]
        });
    });
};

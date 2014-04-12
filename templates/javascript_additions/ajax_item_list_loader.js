
// Loads school list tab and makes the list a dataTable (search functionality, etc.)
function load_item_list(item_tab_id, item_table_id, item_list_url, n_headings_to_exclude) {
    var exclude_headings = new Array();
    for (var back_index = 0; back_index < n_headings_to_exclude; back_index++)
        exclude_headings[back_index] = -n_headings_to_exclude + back_index;
    $('#' + item_tab_id).load(base_url + item_list_url, function() {
        $('#' + item_table_id).dataTable( {
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': exclude_headings }
            ]
        });
    });
};

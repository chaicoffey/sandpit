
// Loads school list tab and makes the list a dataTable (search functionality, etc.)
function load_item_list(item_tab_id, item_table_id, item_list_url) {
    $('#' + item_tab_id).load(base_url + item_list_url, function() {
        $('#' + item_table_id).dataTable( {
            "aoColumnDefs": [
                { 'bSortable': false, 'aTargets': [ -2, -1 ] }
            ]
        });
    });
};


//need to reload active list when an item has been updated
function items_in_list_updated_event(do_after_load_method) {
    base_url = window.location.protocol + "//" + window.location.host;
    list_url = $('#main_view_links li.active a').attr('href');
    n_headings_to_exclude = parseInt(
        $('#main_view_links li.active').attr('load_type').substr('item_list'.length + 1), 10
    );
    load_data_table('main_view', base_url + list_url, n_headings_to_exclude, do_after_load_method);
}

//load class to main window when a class load link in clicked
function class_load_link_clicked_event(link_url, do_after_load_method) {
     load_link_clicked_event(link_url, do_after_load_method)
}

//load percentile graphs to main window when a percentile load link in clicked
function percentile_load_link_clicked_event(link_url, do_after_load_method) {
    load_link_clicked_event(link_url, do_after_load_method)
}

function load_link_clicked_event(link_url, do_after_load_method) {
     base_url = window.location.protocol + "//" + window.location.host;
    $('#main_view').load(base_url + link_url, do_after_load_method)
}
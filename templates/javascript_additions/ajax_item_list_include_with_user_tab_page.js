
//need to reload active list when an item has been updated
function items_in_list_updated_event()
{
    base_url = window.location.protocol + "//" + window.location.host;
    list_url = $('#main_view_links li.active a').attr('href');
    $('#main_view').load(base_url + list_url);
}

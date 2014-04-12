
var base_url = window.location.protocol + "//" + window.location.host;

// Load school list when page is first accessed.
$(document).ready(function(){
    load_item_list('school_list_tab', 'school_list', '/school/list/', 2);
});

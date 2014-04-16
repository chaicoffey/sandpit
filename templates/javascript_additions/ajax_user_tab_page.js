
//for loading from side bar links into main window
$('#main_view_links li a').click(function(event){

    var children = $('#main_view_links').children('li');
    children.each(function(index){$(this).removeClass('active');});
    $(this).parent('li').addClass('active');

    event.preventDefault();
    items_in_list_updated_event();

});

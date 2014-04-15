
//for loading from side bar links into main window
$('#main_view_links li a').click(function(event){

    base_url = window.location.protocol + "//" + window.location.host;
    event.preventDefault();
    $('#main_view').load(base_url + $(this).attr('href'));

    var children = $('#main_view_links').children('li');
    children.each(function(index){$(this).removeClass('active');});
    $(this).parent('li').addClass('active');

});

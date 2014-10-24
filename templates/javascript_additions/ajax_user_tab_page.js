
//for selecting the home tab when the page loads
$(document).ready(function(){
    var children = $('#main_view_links').children('li');
    children.each(function(index){
        if($(this).attr('load_type') == 'user_home_page') {
            $(this).addClass('active');
        }
    });
    load_main_view()
});

//for loading from side bar links into main window
$('#main_view_links li a').click(function(event){

    $('#main_view_links').children('li.active').removeClass('active');
    $(this).parent('li').addClass('active');
    $(this).blur();

    event.preventDefault();

    load_main_view();

});

$('.short_instructions_links li a').click(function(event){

    $('.short_instructions_links').children('li.active').removeClass('active');
    $(this).parent('li').addClass('active');
    $(this).blur();

    event.preventDefault();

    var step_number = parseInt($(this).attr('value'));
    show_short_step(step_number);

});

function show_short_step(step_number) {

    $('.Short_Instructions_Showing').each(function(){
        $(this).removeClass('Short_Instructions_Showing');
        $(this).css('display', 'none');
    })

    var element = $("#short_step_instruction_" + step_number);
    if(element) {
        element.addClass('Short_Instructions_Showing');
        element.css('display', 'inherit');
    }

}

function close_short_instructions() {
    $('.short_instructions_links').children('li.active').removeClass('active');
    show_short_step(-1);

}

function load_main_view() {
    load_type = $('#main_view_links li.active').attr('load_type');
    if(string_starts_with(load_type, 'item_list'))
        items_in_list_updated_event();
    else if(string_starts_with(load_type, 'user_home_page')){
        base_url = window.location.protocol + "//" + window.location.host;
        list_url = $('#main_view_links li.active a').attr('href');
        $('#main_view_bottom').load(base_url + list_url);
        $('#main_view_top').empty();
    } else {
        base_url = window.location.protocol + "//" + window.location.host;
        list_url = $('#main_view_links li.active a').attr('href');
        $('#main_view_bottom').load(base_url + list_url);
        $('#main_view_top').empty();
    }
}

function string_starts_with(full_string, start_string) {
    return (full_string.length >= start_string.length) &&
        (full_string.substring(0, start_string.length) === start_string);
}


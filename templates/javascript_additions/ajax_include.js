
// Must define the items_in_list_updated_event(), class_load_link_clicked_event() and
// percentile_load_link_clicked_event() in another .js to go with this.  It can use the below helper function
// load_data_table().

//helper function for loading the item list table and applying search and sort functionality
function load_data_table(parent_id, item_list_url, n_headings_to_exclude, do_after_load_method) {
    var exclude_headings = new Array();
    for (var back_index = 0; back_index < n_headings_to_exclude; back_index++)
        exclude_headings[back_index] = -n_headings_to_exclude + back_index;
    $('#' + parent_id).load(item_list_url, function(){
        $('#' + parent_id + ' .item_list_table').dataTable({"aoColumnDefs": [{ 'bSortable': false, 'aTargets': exclude_headings }]});
        if(!(typeof do_after_load_method === "undefined"))
            do_after_load_method();
    });
}

//for loading modal links on item_list page into remote modal
$(document).on('click', '.modal_load_link a', function(event){
    event.preventDefault();
    $('#remoteModalContent').load(base_url + $(this).attr('href'), function(){
        $('#modal_submit_button').val('null_submit');
        $('#remoteModal').modal('show');
    });
});

//for loading modal links on item_list page into remote modal
$(document).on('click', '.item_list_modal_load_link a', function(event){
    event.preventDefault();
    $('#remoteModalContent').load(base_url + $(this).attr('href'), function(){
        $('#modal_submit_button').val('item_list_submit');
        $('#remoteModal').modal('show');
    });
    $('#item_list_message_alert').addClass('hidden');
});

//for loading modal links on class results table into remote modal
$(document).on('click', '.class_results_modal_load_link a', function(event){
    event.preventDefault();
    $('#remoteModalContent').load(base_url + $(this).attr('href'), function(){
        $('#modal_submit_button').val('class_results_table_submit');
        $('#remoteModal').modal('show');
    });
    $('#class_user_message_alert').addClass('hidden');
});

//for loading class load links on item_list page
$(document).on('click', '.class_load_link a', function(event){
    event.preventDefault();
    class_load_link_clicked_event($(this).attr('href'), function(){
        $('#class_results').load(base_url + $('#class_results').attr('href'));
    })
});

//for loading class load links on item_list page
$(document).on('click', '.class_result_edit_page_load_link a', function(event){
    event.preventDefault();
    $('#class_results').load(base_url + $(this).attr('href'));
});

//for loading percentile load links
$(document).on('click', '.percentile_load_link a', function(event){
    event.preventDefault();
    percentile_load_link_clicked_event($(this).attr('href'));
});

//for loading test instructions load links
$(document).on('click', '.test_instructions_load_link a', function(event){
    $(this).attr('target', '_blank')
});

//for loading percentile load links on age_gender_selection change
$(document).on('change', '#age_gender_selection', function(event){
    event.preventDefault();
    percentile_load_link_clicked_event($('#age_gender_selection').val());
});

//for loading from a load in class page form submit to class page
$(document).on('submit', '.load_in_class_page', function(formEvent) {

    formEvent.preventDefault();

    var form = $('.load_in_class_page');

    var options = {
        url: form.attr('action'),
        error: function(response) {
            $('#class_results').html("An error occurred accessing form");
        },
        success: function(response) {
            $('#class_results').html(response);
        }
    };

    $('.load_in_class_page').ajaxSubmit(options);

});

//for loading from a modal form submit to modal window (if form in response) or update the list (if no form in response)
$(document).on('submit', '#modalForm', function(formEvent) {

    formEvent.preventDefault();

    var form = $('#modalForm');
    var button_value = $('#modal_submit_button').attr('value');
    $("#progress-bar").removeClass('hide');

    var options = {
        url: form.attr('action'),
        error: function(response) {
            $('#remoteModalContent').html("An error occurred accessing modal form");
        },
        success: function(response) {
            user_message_element = $(response).find('.user_message');
            user_error_message_element = $(response).find('.user_error_message');
            if($(user_message_element).length) {
                close_modal_and_update_list(button_value, user_message_element);
            } else if($(user_error_message_element).length) {
                close_modal_and_update_list(button_value, user_error_message_element);
            } else {
                $('#remoteModalContent').html(response);
                $('#modal_submit_button').val(button_value)
            }
        }
    };

    $('#modalForm').ajaxSubmit(options);

});

function close_modal() {
    $('#remoteModal').modal('hide');
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
}

function close_modal_and_update_list(button_value, user_message_element) {

    base_url = window.location.protocol + "//" + window.location.host;
    close_modal();
    if(button_value == 'item_list_submit') {
        items_in_list_updated_event(function(){
            $('#item_list_user_message').html(user_message_element);
            $('#item_list_user_message_alert').removeClass('hidden');
        });
    } else if(button_value == 'class_results_table_submit') {
        $('#class_results').load(base_url + $('#class_results').attr('href'), function(){
            $('#class_user_message').html(user_message_element);
            $('#class_user_message_alert').removeClass('hidden');
        })
    }
}

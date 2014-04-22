
//must define the items_in_list_updated_event() in another .js to go with this.
//it can use the helper function below.

//helper function for loading the item list table and applying search and sort functionality
function load_data_table(parent_id, item_list_url, n_headings_to_exclude, do_after_load_method) {
    var exclude_headings = new Array();
    for (var back_index = 0; back_index < n_headings_to_exclude; back_index++)
        exclude_headings[back_index] = -n_headings_to_exclude + back_index;
    $('#' + parent_id).load(item_list_url, function(){
        $('#item_list_table').dataTable({"aoColumnDefs": [{ 'bSortable': false, 'aTargets': exclude_headings }]});
        if(!(typeof do_after_load_method === "undefined"))
            do_after_load_method();
    });
}

//for loading modal links on item_list page into remote modal
$(document).on('click', '.modal_load_link a', function(event){
    event.preventDefault();
    $('#remoteModalContent').load(base_url + $(this).attr('href'), function(){
        $('#remoteModal').modal('show');
    });
    $('#item_list_user_message_alert').addClass('hidden');
});

//for loading load links on item_list page
$(document).on('click', '.class_load_link a', function(event){
    event.preventDefault();
    class_load_link_clicked_event($(this).attr('href'), function(){
        load_data_table('class_students', base_url + $('#class_students').attr('href'), 1)
    })
});

//for loading from a modal form submit to modal window (if form in response) or update the list (if no form in response)
$(document).on('submit', '#modalForm', function(formEvent) {

    formEvent.preventDefault();

    var form = $('#modalForm');

    var options = {
        url: form.attr('action'),
        error: function(response) {
            $('#remoteModalContent').html("An error occurred accessing modal form");
        },
        success: function(response) {
            user_message_element = $(response).find('.user_message');
            user_error_message_element = $(response).find('.user_error_message');
            if($(user_message_element).length) {
                close_modal_and_update_list(function(){
                    $('#item_list_user_message').html(user_message_element);
                    $('#item_list_user_message_alert').removeClass('hidden');
                });
            } else if($(user_error_message_element).length) {
                close_modal_and_update_list(function(){
                    $('#item_list_user_message').html(user_error_message_element);
                    $('#item_list_user_message_alert').removeClass('hidden');
                });
            } else
                $('#remoteModalContent').html(response);
        }
    };

    $('#modalForm').ajaxSubmit(options);

});

function close_modal_and_update_list(do_after_load_method) {
    $('#remoteModal').modal('hide');
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
    items_in_list_updated_event(do_after_load_method);
}

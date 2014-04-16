
//must define the items_in_list_updated_event() in another .js to go with this.
//it can use the helper function below.

//helper function for loading the item list table and applying search and sort functionality
function load_data_table(parent_id, item_list_url, n_headings_to_exclude) {
    var exclude_headings = new Array();
    for (var back_index = 0; back_index < n_headings_to_exclude; back_index++)
        exclude_headings[back_index] = -n_headings_to_exclude + back_index;
    $('#' + parent_id).load(item_list_url, function(){
        $('#item_list_table').dataTable({"aoColumnDefs": [{ 'bSortable': false, 'aTargets': exclude_headings }]});
    });
};

//for loading modal links on item_list page into remote modal
$(document).on('click', '.modal_load_link a', function(event){
    event.preventDefault();
    $('#remoteModalContent').load(base_url + $(this).attr('href'), function(){
        $('#remoteModal').modal('show');
    });
});

//for loading from a modal form submit to modal window
$(document).on('submit', '#modalForm', function(formEvent) {

    formEvent.preventDefault();

    var form = $('#modalForm');

    var options = {
        url: form.attr('action'),
        error: function(response) {
            $('#remoteModalContent').html("An error occurred accessing modal form");
        },
        success: function(response) {
            $('#remoteModalContent').html(response);
        }
    };

    $('#modalForm').ajaxSubmit(options);

});

//for updating the list when model finished button is clicked
$(document).on('click', '#modal_close_button', function() {
    $('#remoteModal').modal('hide');
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
    items_in_list_updated_event();
});


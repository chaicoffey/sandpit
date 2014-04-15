
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


// Clear contents of remote modal when it is hidden so that it can be loaded with new contents next time it is accessed.
$(document).on('hidden.bs.modal', '#remoteModal', function() {
    $('#remoteModal').removeData('bs.modal');
});

//loads modal form window after submission from the modal window
$(document).on('submit', '#modalForm', function(formEvent) {

    formEvent.preventDefault();
    var form = $('#modalForm');
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function(data, textStatus, jqXHR){
            $("#remoteModal .modal-content").html(data);
        },
        error: function(data, textStatus, jqXHR){
            $("#remoteModal .modal-content").html("An error occurred accessing modal form");
        }
    });

});
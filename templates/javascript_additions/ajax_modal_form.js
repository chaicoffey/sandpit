
// Clear contents of remote modal when it is hidden so that it can be loaded with new contents next time it is accessed.
$(document).on('hidden.bs.modal', '#remoteModal', function() {
    $('#remoteModal').removeData('bs.modal');
});


//loads modal form window after submission from the modal window
$(document).on('submit', '#modalForm', function(formEvent) {

    formEvent.preventDefault();
    var form = $('#modalForm');
    var options = {
        url: form.attr('action'),
        error: function(response) {
            $("#remoteModal .modal-content").html("An error occurred accessing modal form");
        },
        success: function(response) {
            $("#remoteModal .modal-content").html(response);
        }
    };

    $('#modalForm').ajaxSubmit(options);

});

// Refresh the school list when the modal close button is clicked
$(document).on('click', '#modal_close_button', function() {
    $('#remoteModal').modal('hide');
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
    loadSchoolList();
});

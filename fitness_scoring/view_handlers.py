
from django.contrib import messages
from fitness_scoring.forms import AddSchoolForm, EditSchoolForm
from fitness_scoring.models import School, Administrator
from fileio import add_schools_from_file_upload


def handle_logged_in(request, context):
    context['user_type'] = request.session.get('user_type', None)
    context['name'] = request.session.get('username', None)


def handle_school_list(request, context):

    school_list_message_tag = "school_list"

    def handle_post_add_schools():
        handle_post = (request.POST.get('SubmitIdentifier') == 'AddSchools')
        if handle_post:
            (n_created, n_updated, n_not_created_or_updated) = add_schools_from_file_upload(request.FILES['add_schools_file'])
            messages.success(request, "Summary of changes made from .CSV: ", extra_tags=school_list_message_tag)
            messages.success(request, "Schools Created: "+str(n_created), extra_tags=school_list_message_tag)
            messages.success(request, "Schools Updated: "+str(n_updated), extra_tags=school_list_message_tag)
            messages.success(request, "No Changes From Data Lines: "+str(n_not_created_or_updated), extra_tags=school_list_message_tag)
        return handle_post

    def handle_post_delete_school():
        handle_post = (request.POST.get('SubmitIdentifier') == 'DeleteSchool')
        if handle_post:
            school_to_delete = School.objects.get(pk=request.POST.get('school_pk'))
            school_name = school_to_delete.name
            if school_to_delete.delete_school_safe():
                messages.success(request, "School Deleted: " + school_name, extra_tags=school_list_message_tag)
            else:
                messages.success(request, "Error Deleting School: " + school_to_delete.name + " (School is being used)", extra_tags=school_list_message_tag)
        return handle_post

    context['administrator_list'] = Administrator.objects.all()
    context['add_school_form'] = AddSchoolForm()
    context['edit_school_form'] = EditSchoolForm()

    post_handled = False

    if request.method == 'POST':
        if not post_handled:
            post_handled = AddSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
        if not post_handled:
            post_handled = EditSchoolForm(request.POST).handle_posted_form(request=request, messages_tag=school_list_message_tag)
        if not post_handled:
            post_handled = handle_post_add_schools()
        if not post_handled:
            post_handled = handle_post_delete_school()

    return post_handled
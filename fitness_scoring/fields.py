from pe_site.settings import MAX_FILE_UPLOAD_SIZE_MB
from django import forms
from django.core.exceptions import ValidationError


class MultiFileInput(forms.FileInput):

    def render(self, name, value, attrs={}):
        attrs['multiple'] = 'multiple'
        return super(MultiFileInput, self).render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return [files.get(name)]


class MultiFileField(forms.FileField):

    widget = MultiFileInput

    default_error_messages = {
        'min_num': u"Ensure at least %(min_num)s files are uploaded (received %(num_files)s).",
        'max_num': u"Ensure at most %(max_num)s files are uploaded (received %(num_files)s).",
        'file_size': u"File: %(uploaded_file_name)s, exceeded maximum upload size."
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 1)
        self.max_num = kwargs.pop('max_num', None)
        self.maximum_file_size = kwargs.pop('maximum_file_size', 1024*1024*MAX_FILE_UPLOAD_SIZE_MB)
        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            ret.append(super(MultiFileField, self).to_python(item))
        return ret

    def validate(self, data):
        super(MultiFileField, self).validate(data)
        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0
        if num_files < self.min_num:
            raise ValidationError('Need To Upload At Least ' + str(self.min_num) + ' File(s)')
        elif self.max_num and (num_files > self.max_num):
            raise ValidationError('Cannot Upload More Than ' + str(self.max_num) + ' File(s)')
        for uploaded_file in data:
            if (self.maximum_file_size is not None) and uploaded_file and (uploaded_file.size > self.maximum_file_size):
                raise ValidationError('File To Large: ' + uploaded_file.name)
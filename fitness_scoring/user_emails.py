import threading
from django.core.mail import send_mail
from pe_site.settings import DEFAULT_FROM_EMAIL


subject_start = 'Fitness Testing App - '

sign_off = ('\n\n'
            'Regards,\n'
            'Fitness testing app team\n')

web_address = 'www.not_sure_yet.com'


def send_email(email, subject, text):
    t = threading.Thread(target=send_mail,
                         args=[subject_start + subject, text + sign_off, DEFAULT_FROM_EMAIL, [email]],
                         kwargs={'fail_silently': True})
    t.setDaemon(True)
    t.start()


def send_group_email(emails, subject, text):
    send_mail(subject_start + subject, text + sign_off, DEFAULT_FROM_EMAIL, emails)


def send_email_user_reset(email, username, password, teacher_or_admin):
    send_email(email,
               ('Teacher' if teacher_or_admin else 'Administrator') + ' Password Reset',
               ('Hi,\n\n'
               'Your' + ('' if teacher_or_admin else ' administrator') + ' password has been reset (details below)\n\n'
               'username: ' + username + '\n'
               'password: ' + password))


def send_email_user_login(email, username, password, teacher_or_admin):
    send_email(email,
               ('Teacher' if teacher_or_admin else 'Administrator') + ' Login Details',
               ('Hi,\n\n'
               'You are now signed up for the fitness testing application.\n\n'
               'To start using go to ' + web_address + ' and enter the login details below:\n\n'
               'username: ' + username + '\n'
               'password: ' + password + '\n\n'
               "After you login just " + ("follow " if teacher_or_admin else "start following ") +
               "the steps and you're away!"))
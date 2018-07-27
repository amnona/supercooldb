import sys
import smtplib
import random
import string
import datetime
import inspect

debuglevel = 6


def debug(level, msg):
    """
    print a debug message

    input:
    level : int
        error level (0=debug, 4=info, 7=warning,...10=critical)
    msg : str
        the debug message
    """
    global debuglevel

    if level >= debuglevel:
        try:
            cf = inspect.stack()[1]
            cfile = cf.filename.split('/')[-1]
            cline = cf.lineno
            cfunction = cf.function
        except:
            cfile = 'NA'
            cline = 'NA'
            cfunction = 'NA'
        print('[%s] [%d] [%s:%s:%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level, cfile, cfunction, cline, msg), file=sys.stderr)
        sys.stdout.flush()


def SetDebugLevel(level):
    global debuglevel

    debuglevel = level


def getdoc(func):
    """
    return the json version of the doc for the function func

    input:
    func : function
        the function who's doc we want to return

    output:
    doc : str (html)
        the html of the doc of the function
    """
    print(func.__doc__)
    s = func.__doc__
    s = "<pre>\n%s\n</pre>" % s
    return(s)


def tolist(data):
    """
    if data is a string, convert to [data]
    if already a list, return the list

    input:
    data : str or list of str

    output:
    data : list of str
    """
    if isinstance(data, str):
        return [data]
    return data


def send_email(user, pwd, recipient, subject, body):
    import os

    if 'OPENU_FLAG' in os.environ:
        debug(1, 'Sending mail using openu server')
        openu_str = "echo '%s' | mail -s '%s' -r %s %s" % (body, subject, ' dbbact@openu.ac.il', recipient)
        os.system(openu_str)
        return

    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        return ('successfully sent the mail')
    except:
        return ('failed to send mail')


def random_str(size=6, chars=string.ascii_uppercase + string.digits):
    """
    generate str which can be used as a password

    output:
    random str : string of 6 characters
    """
    return ''.join(random.choice(chars) for _ in range(size))

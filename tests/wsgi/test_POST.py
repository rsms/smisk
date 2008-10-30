'''This module exposes the post bug that Eric Moritz is experiences

where smisk segfaults

:See: Fixed in 77188bce80d5 <http://hg.hunch.se/smisk/diff/77188bce80d5/src/Stream.c>
'''
from smisk import wsgi
import smisk.core
from StringIO import StringIO

def safe_copyfileobj(fsrc, fdst, length=16*1024, size=0):
    '''
    A version of shutil.copyfileobj that will not read more than 'size' bytes.
    This makes it safe from clients sending more than CONTENT_LENGTH bytes of
    data in the body.
    '''
    if not size:
        return
    while size > 0:
        buf = fsrc.read(min(length, size))
        if not buf:
            break
        fdst.write(buf)
        size -= len(buf)


# I think this is the offender, taken from Django's WSGIRequest object in 
# django.core.handlers.wsgi
def _get_raw_post_data(environ):
    buf = StringIO()
    try:
        # CONTENT_LENGTH might be absent if POST doesn't have content at all (lighttpd)
        content_length = int(environ.get('CONTENT_LENGTH', 0))
    except ValueError: # if CONTENT_LENGTH was empty string or not an integer
        content_length = 0
    if content_length > 0:
        safe_copyfileobj(environ['wsgi.input'], buf,
                         size=content_length)
    _raw_post_data = buf.getvalue()
    buf.close()
    return _raw_post_data


def WSGIPostTest(environ, start_request):

    if environ['REQUEST_METHOD'] == 'GET':
        fh = file("./html/test_POST.html")
        lines = fh.readlines()
        fh.close()
        start_request("200 OK", [])
        return lines
    elif environ['REQUEST_METHOD'] == 'POST':
        raw_post_data = _get_raw_post_data(environ)
        start_request("200 OK", [])
        return [raw_post_data]

smisk.core.bind("127.0.0.1:3030")
wsgi.Application(WSGIPostTest).run()

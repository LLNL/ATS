import time

def getName(name='',sleep=1,arch=''):
    """return a string based on input name.
       The purpose is to reduce or eliminate the name collision issue.
       Original arguments (withTime, numProcs, short) are deleted as
       they are not used at all in all tests invoked.
       if sleep > 0, sleep for sleep seconds to give unique name.
       """

    result = ''
    if name:
        result += name + '_'

    if arch:
        result += arch + '_'

    # if getName is called two or more times quickly,
    # it results in the name collision issue unless using
    # distinct NAME or sleep 1 sec if using the same NAME.
    if sleep: time.sleep(sleep)

    result += time.strftime('%y%m%d%H%M%S',time.localtime())

    return result

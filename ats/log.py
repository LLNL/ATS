import sys, os
from ats.atsut import abspath

class AtsLog(object):
    "Log and stderr echo facility"
    def __init__(self, directory = '', name='',
                 echo=True, logging = False, indentation='   '):
        super(AtsLog, self).__init__ ()
        self.reset()
        self.echo=echo
        self.leading = ''
        self.indentation=indentation
        self.mode = "w"
        self.logging = False  #temporary
        self.set(directory=directory, name = name)
        self.logging = logging

    def set(self, directory = '', name = ''):
        "Set the name and directory of the log file."
        if not directory:
            directory = os.getcwd()
        if not name:
            name = "ats.log"
        self.directory = abspath(directory)
        self.shortname = name
        self.name = os.path.join(self.directory, self.shortname)

    def reset(self):
        "Erase indentation history."
        self.__previous = []

    def _open(self, filename, mode):
        try:
            return open(filename, mode)
        except IOError:
            pass
        if not os.path.isdir(self.directory):
            os.makedirs(self.directory)
        return open(filename, mode)

    def putlist(self, linelist, **kw):
        """Write a list of lines that include newline at end.
           Keywords echo and logging.
        """
# doesn't seem worth it to check for bad keywords
        echo = kw.get('echo', self.echo)
        logging = kw.get('logging', self.logging)
        indentation=self.leading
        if logging:
            d = self._open(self.name, self.mode)
            self.mode = 'a'
            for line in linelist:
                print(indentation + line, file=d)
            print('', file=d)
            d.close()

        if echo:
            d = sys.stderr
            for line in linelist:
                print(indentation + line, file=d)
            print('', file=d)

    def write(self, *items, **kw):
        "Write one line, like a print. Keywords echo and logging."
        echo = kw.get('echo', self.echo)
        logging = kw.get('logging', self.logging)
        if not echo and not logging:
            return

        content = self.leading + ' '.join([str(k) for k in items])

        #
        # 2017-12-07 SAD try to keep the terminal sane on blueos (rzmanta)
        #
        from ats import configuration
        if configuration.SYS_TYPE.startswith('blueos'):

            if "ENVIRONMENT" in os.environ.keys():
                my_environment = os.environ.get("ENVIRONMENT", 'novalue')

            if my_environment == "INTERACTIVE":
                # print ("SAD DEBUG calling stty sane. ENVIRONMENT variable is '%s'" % (my_environment))
                os.system("stty sane") # Keep interactive terminal sane

        # printing of long lines is causing errors on some systems.  Split the line into smaller lines
        if configuration.SYS_TYPE.startswith('somesystemxxx'):
            n = 200
            lines = [content[i:i+n] for i in range(0, len(content), n)]
        else:
            lines = [content]

        indented_lines = "\n    ".join(lines)
        if echo:
            # if len(indented_lines) < 512:
            #     print(indented_lines, file=sys.stderr)
            # else:
            #     print(indented_lines[0:512], file=sys.stderr)
            print(indented_lines[0:4096], file=sys.stderr)
        if logging:
            if not os.path.isdir(self.directory):
                os.makedirs(self.directory)
            with open(self.name, 'a') as log_file:
                print(indented_lines, file=log_file)

    __call__ = write

    def indent(self):
        self.__previous.append(self.leading)
        self.leading += self.indentation

    def dedent(self):
        try:
            self.leading = self.__previous.pop()
        except IndexError:
            pass

    def fatal_error(self, msg):
        "Issue message and die."
        try:
            self('Fatal error:', msg, echo=True)
        except Exception:
            print(msg, file=sys.stderr)
        raise SystemExit(1)

log = AtsLog(name="ats.log")
terminal = AtsLog(echo=True, logging=False)

if __name__ == "__main__":
    log = AtsLog(logging=True, directory='test.logs')
    print("%s%s%s" % (log.directory, log.name, log.shortname))
    log('a','b','c')
    log.indent()
    log('this should be indented')
    log('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    log.dedent()
    list1 =  ['unindent here',
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
        'ccccccccccccc',
        'ddddddddddddddddddddddddddddddddddddddd',
        'ddddddddddddddddddddddddddddddddddddddd',
        'ddddddddddddddddddddddddddddddddddddddd',
        'ddddddddddddddddddddddddddddddddddddddd',
        'ddddddddddddddddddddddddddddddddddddddd',
        'ddddddddddddddddddddddddddddddddddddddd'
        ]
    for line in list1:
        log(line)
    terminal('this to terminal')

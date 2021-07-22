import os
import subprocess

import logs

__all__=('EFFORT_ONLY_OUTPUT_STREAM','Command')

EFFORT_ONLY_OUTPUT_STREAM = 'This empty output stream is the output of an EffortOnly command.'

class UsageError(Exception):
    """The user requested something unreasonable.

    Usual issue: executable not found.
    """
    def __init__(self, message):
        super(UsageError, self).__init__()
        self.message = message
    def __str__(self):
        return 'Usage error.  %s' % self.message

class CommandRunner(object):
    """Shell command implementation base class"""

    def __init__(self, logger=None, effort_only=False) :
        """Initializes the instance variables associated with the class
        """
        self.effort_only = effort_only
        if logger is None:
            self._logger=logs.getLogger('root')
        else:
            self._logger=logger

    def issueCommand(self, args) :
        """Issue the command associated with the given Popen arguments list.
            Returns the output of the command as a string, if any.
        """
        unused = logs.ScopeLoggers(self._logger, __name__)
        if self.effort_only:
            self._logger.debug('WOULD RUN: %s ' % args)
            Output_Stream = EFFORT_ONLY_OUTPUT_STREAM
        else:
            self._logger.debug('RUNNING: %s ' % args)
            try :
                p1 = subprocess.Popen(
                    args,
                    env=os.environ,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                Output_Stream = p1.communicate()[0]
            except OSError as e :
                if e.errno==2:
                    message = 'Execution of command "%s" failed.  %s.' %\
                                        (args[0], e.strerror)
                    raise UsageError(message)
                else:
                    raise
        return Output_Stream

    def issueFirstCommand(self, commandList, argList) :
        """Issues the first command found in commandList, using the
        arguments in argList.

            The parameters should each be lists of strings.
            Returns the output of the command as a string, if any.
        """
        unused = logs.ScopeLoggers(self._logger, __name__)
        for command in commandList:
            if os.path.isfile(command):
                return self.issueCommand ([command,] + argList)
            self._logger.debug('Command "%s" not found.' % command)
        message = 'Execution of command failed.  None of %s found.' % \
                  str(commandList)
        raise UsageError(message)


def demo_command():
    logger=logs.getLogger('demo_command')
    logger.info('Demonstrating command execution.\n')
    command = CommandRunner(logger=logger)

    def demoAtLevel(level):
        logger.setLevel(level)

        args = ['/bin/ls', '/']
        for effort_only in (True, False):
            command.effort_only = effort_only
            logger.info('Running command with effort_only=%s:\n' %
                     effort_only + '-'*80)
            Results_Stream = command.issueCommand(args)
            logger.info('Output: \n%s\n' % Results_Stream)

        logger.info('Running non-existent command:\n' + '-'*80)
        args = ['bogus_command', '/']
        try:
            command.issueCommand(args)
        except UsageError as e:
            logger.info('Caught expected exception:\n%s\n' % e)

        logger.info('Running first command found:\n' + '-'*80)
        commandList = ['/bin/foo', '/bin/ls']
        argList = ['/',]
        Results_Stream = command.issueFirstCommand(commandList, argList)
        logger.info('Output: \n%s\n' % Results_Stream)

        logger.info('Running non-existent commands:\n' + '-'*80)
        commandList = ['/bin/foo', '/bin/bar']
        argList = ['/',]
        try:
            command.issueFirstCommand(commandList, argList)
        except UsageError as e:
            logger.info('Caught expected exception:\n%s\n' % e)

    logger.info ('Demo with normal output.\n' + '='*80 + '\n')
    demoAtLevel(logs.INFO)
    logger.info ('Demo with verbose/debug output:\n' + '='*80 + '\n')
    demoAtLevel(logs.DEBUG)
    logger.info('\n\nDemo complete. No unexpected exceptions raised.')

if __name__ == '__main__':
    demo_command()

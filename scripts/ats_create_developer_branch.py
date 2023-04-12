#!/usr/bin/env python3

import os, sys, re, subprocess
import argparse

# ----------------------------------------------------------------------------------------------------------------------
# Use Examples
#
# ats_create_developer_branch.py feature
# ats_create_developer_branch.py user feature
#
# If given with 1 arguments, the user will be determined by using whoami
# If given with 2 arguments, the user may be set by hand
#
# Both the user and the feature must be simple strings (alphanumeric plus '_' or '-')
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# Simple support routines
# ----------------------------------------------------------------------------------------------------------------------
def error_and_exit(code, messages):
    print("ATS ERROR: ------------------------------------------------------------------------")
    print("ATS ERROR:         C R E A T E   D E V E L O P E R   B R A N C H   A B E N D")
    for mess in messages:
        print("ATS ERROR: %s" % mess)
    print("ATS ERROR: ------------------------------------------------------------------------")
    sys.exit(code)

def warning_but_continue(messages):
    print("ATS WARNING: ----------------------------------------------------------------------")
    for mess in messages:
        print("ATS WARNING: %s" % mess)
    print("ATS WARNING: ----------------------------------------------------------------------")

def yes_or_no(question, default_to_yes):
    if default_to_yes:
        print(question + ' (y/n): y')
        return True
    while "the answer is invalid":
        reply = str(input(question+' (y/n): ')).lower().strip()
        if len(reply) < 1:
            continue
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False

def runcommand_die_on_err (cmd):
    print("Executing: %s" % cmd)
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)
    std_out, std_err = proc.communicate()

    if proc.returncode != 0:
        messages = []
        messages.append("%s" % cmd)
        messages.append("failed with return code %i" % proc.returncode)
        messages.append("%s" % std_out)
        messages.append("%s" % std_err)
        error_and_exit(proc.returncode, messages)

    return proc.returncode, std_out, std_err

def parse_arguments(args):
    parser = argparse.ArgumentParser(description='Script to create a developer branch for the MC project')

    parser.add_argument('-f', '--feature',
                        help='REQUIRED (or --bugfix, specify either not both): short description of the feature to be developed (used in branch name)')

    parser.add_argument('-b', '--bugfix',
                        help='REQUIRED (or --feature, specify either not both): short description of the bugfix (used in branch name)')

    parser.add_argument('-u', '--user',
                        help='OPTIONAL: developer name to be used when creating the branch (used in branch name)')

    parser.add_argument('-y', '--yes', action='store_true',
                        help='OPTIONAL: assume yes to all script command line prompts')

    return parser, parser.parse_args(args)

# ----------------------------------------------------------------------------------------------------------------------
# main driver
# ----------------------------------------------------------------------------------------------------------------------
if __name__=="__main__":

    # -------------------------------------------------------------------------
    # Help Screen
    # and process command line arguments
    # -------------------------------------------------------------------------
    parser, args = parse_arguments(sys.argv[1:])

    if args.feature is None and args.bugfix is None:
        parser.print_help()
        sys.exit(-1)

    if args.feature is not None and args.bugfix is not None:
        parser.print_help()
        sys.exit(-1)

    if args.user is None:
        args.user = os.popen('whoami').read()
        args.user = args.user.rstrip()

    # -------------------------------------------------------------------------
    # Restrict the characters in the user and feature strings (branch name)
    # -------------------------------------------------------------------------
    if args.feature is not None:
        if not re.match(r'^[A-Za-z0-9_-]+$', args.feature):
            print("feature '%s' is invalid.  Must be alphanumeric (plus - and _)" % args.feature)
            print("Exiting without creating branch.")
            sys.exit(-1)

    if args.bugfix is not None:
        if not re.match(r'^[A-Za-z0-9_-]+$', args.bugfix):
            print("bugfix '%s' is invalid.  Must be alphanumeric (plus - and _)" % args.bugfix)
            print("Exiting without creating branch.")
            sys.exit(-1)

    if not re.match(r'^[A-Za-z0-9_-]+$', args.user):
        print("user '%s' is invalid.  Must be alphanumeric (plus - and _)" % args.user)
        print("Exiting without creating branch.")
        sys.exit(-1)

    # -------------------------------------------------------------------------
    # Do some verification and introspection on the git repo.
    # -------------------------------------------------------------------------
    if not os.path.isdir(".git"):
        error_and_exit(-1, [".git directory not found", "Please run this script from the top level of git clone"])

    code, out, err = runcommand_die_on_err('git config --get remote.origin.url');
    remote_repo = out.rstrip()

    repoVersionFile = "ats/src/ats/version.py"
    majorToken = "ATS_MAJOR"
    minorToken = "ATS_MINOR"
    patchToken = "ATS_PATCH"

    if not os.path.isfile(repoVersionFile):
        messages = ["Expected version file %s does not exist" % repoVersionFile]
        error_and_exit(-1, messages)

    code, out, err = runcommand_die_on_err("git branch | grep \* | cut -d ' ' -f2");
    local_branch = out.rstrip()

    if local_branch.startswith('feature'):
        local_branch_type = "feature"
    if local_branch.startswith('bugfix'):
        local_branch_type = "bugfix"
    elif local_branch.startswith('release'):
        local_branch_type = "release"
    elif local_branch.startswith('main'):
        local_branch_type = "main"
    else:
        local_branch_type = "unknown"

    print("Info: remote repo ............: %s" % remote_repo)
    print("Info: version header file ....: %s" % repoVersionFile)
    print("Info: checked out branch .....: %s" % local_branch)
    print("Info: checked out branch type : %s" % local_branch_type)

    if local_branch_type != "main":
        messages = ["This script restricted to only operate within a clone of the 'main' branch"]
        error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Inspect the state of the local branch.  If there is uncommitted work
    # or unpushed work, then do not continue.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err("git status --porcelain");
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')

    if len(git_status_lines) == 1 and git_status_lines[0] == '':
        print("Info: local clone looks clean ... continuing")
    else:
        messages = ["Unsure of status of local branch %s. Will not continue" % local_branch]
        messages.append("")
        for line in git_status_lines: messages.append(line)
        error_and_exit(-1, messages)

    # the git pull puts messages in err. So catenate out and err strings.
    code, out, err = runcommand_die_on_err("git pull --dry-run");
    git_pull_dry_run = out.rstrip() + err.rstrip()
    git_pull_dry_run_lines = git_pull_dry_run.split('\n')

    # do not update if it looks like we need to pull.
    if "bitbucket" in git_pull_dry_run and "From" in git_pull_dry_run:
        messages = ["Local branch %s needs to be pulled" % local_branch]
        messages.append("")
        for line in git_pull_dry_run_lines: messages.append(line)
        error_and_exit(-1, messages)
    # do not update if we are unsure of the results of the pull (if there are >1 line in the output)
    if len(git_pull_dry_run_lines) > 1:
        messages = ["Unsure of status of local branch %s. Will not continue" % local_branch]
        messages.append("")
        for line in git_pull_dry_run_lines: messages.append(line)
        error_and_exit(-1, messages)


    # -------------------------------------------------------------------------
    # Tell user what we are going to do and prompt y/n to accept.
    # -------------------------------------------------------------------------
    if args.feature is not None:
        branch_name = '%s/%s/%s' % ("feature", args.user, args.feature)
    elif args.bugfix is not None:
        branch_name = '%s/%s/%s' % ("bugfix", args.user, args.bugfix)
    else:
        # redundant, but I don't like else assumptions
        parser.print_help()
        sys.exit(-1)

    question = "Do you want to create branch '%s'" % branch_name
    answer = yes_or_no(question, args.yes)
    if answer == False:
        print("Exiting without creating branch '%s'" % branch_name)
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Now do the commands needed to create the developer branch push it to
    # the Bit Bucket repo and set it's origin correctly
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('git checkout -b %s' % branch_name);

    question = "Do you want to push developer branch '%s' to the remote repo %s" % (branch_name, remote_repo)
    answer = yes_or_no(question, args.yes)
    if answer == False:
        print("Exiting without pushing developer branch to the repo %s" % branch_name)
        sys.exit(0)

    code, out, err = runcommand_die_on_err('git push --set-upstream origin %s' % branch_name);

# ----------------------------------------------------------------------------------------------------------------------
# end of file
# ----------------------------------------------------------------------------------------------------------------------

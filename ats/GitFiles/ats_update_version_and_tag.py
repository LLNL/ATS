#!/usr/bin/env python3

import os, sys, re, subprocess
import argparse

# ----------------------------------------------------------------------------------------------------------------------
# This script is used to update the version header files and tag the branch with this same version number
#
# When invoked with no arguments, will detect the last patch level,increment it by 1, and use that.
# Optionally, a full major.minor.patch number may be given.  in this instance, it will be error checked a few ways
#   to ensure it is acceptable.
#
# As part of this process a 'git pull' will occurr to get the local branch up to date with the remote (bit bucket)
# repo.  There must be no modifications to the local repo which have not been pushed to the remote
# repo already.
#
# When using this,the repo must be in a clean state, with not uncommitted source changes.  This script should do
# exactly tow things -- update the version file and tag.  It should not make any other source code commits.
#
# Use Example:
# ats_update_version_and_tag.py 
# ats_update_version_and_tag.py --version 5.18.3
# ats_update_version_and_tag.py --bypass
#
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# Simple support routines
# ----------------------------------------------------------------------------------------------------------------------
def error_and_exit(code, messages):
    print("Error: ------------------------------------------------------------------------")
    print("Error:              U P D A T E   A N D   T A G   A B E N D")
    print("Error:")
    for mess in messages:
        print("Error: %s" % mess)
    print("Error: ------------------------------------------------------------------------")
    sys.exit(code)

def warning_but_continue(messages):
    print("Warning: ----------------------------------------------------------------------")
    for mess in messages:
        print("Warning: %s" % mess)
    print("Warning: ----------------------------------------------------------------------")

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

def runcommand_die_on_err (cmd, echoCmd=True):
    if echoCmd:
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
    parser = argparse.ArgumentParser(description='Script to updte the version header file and tag a branch.')

    parser.add_argument('-b', '--bypass', action='store_true',
                        help='OPTIONAL: Bypass (do no work and exit script) if no remote updates have occured')

    parser.add_argument('-v', '--version',
                        help='OPTIONAL: major.minor.patch to use such as 5.18.3')

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

    # -------------------------------------------------------------------------
    # Verify that .git exists in the current directory.
    # -------------------------------------------------------------------------
    if not os.path.isdir(".git"):
        error_and_exit(-1, [".git directory not found", "Please run this script from the top level of git clone"])

    # -------------------------------------------------------------------------
    # Determine the repo repo.
    # Determine the current local branch checked out name and type
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('git config --get remote.origin.url', False);
    remote_repo = out.rstrip()

    repoVersionFile = "src/ats/version.py"
    majorToken = "ATS_MAJOR"
    minorToken = "ATS_MINOR"
    patchToken = "ATS_PATCH"


    if not os.path.isfile(repoVersionFile):
        messages = ["Expected version file %s does not exist" % repoVersionFile]
        error_and_exit(-1, messages)

    code, out, err = runcommand_die_on_err("git branch | grep \* | cut -d ' ' -f2", False);
    local_branch = out.rstrip()

    if local_branch.startswith('feature'):
        local_branch_type = "feature"
    elif local_branch.startswith('release'):
        local_branch_type = "release"
    elif local_branch.startswith('master'):
        local_branch_type = "master"
    else:
        local_branch_type = "unknown"

    print("Info: remote repo ............: %s" % remote_repo)
    print("Info: version header file ....: %s" % repoVersionFile)
    print("Info: checked out branch .....: %s" % local_branch)
    print("Info: checked out branch type : %s" % local_branch_type)

    if local_branch_type == "feature" or local_branch_type == "unknown":
        messages = ["This script restricted to only operate on 'master' or 'release' branches"]
        error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Inspect the state of the local branch.  If there is uncommitted work
    # or unpushed work, then do not continue.
    #
    # 2019-09-11 SAD Note.
    # I am being quite cautious here.  There should be no uncommitted or 
    # or modified work on the local branch.  Similarly, there should be no
    # need to do a pull from the remote bitbucket repo.  We may loosen
    # these restritions in the future.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err("git status --porcelain", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')

    if len(git_status_lines) == 1 and git_status_lines[0] == '':
        print("Info: local clone looks clean : continuing")
    else:
        messages = ["Unsure of status of local branch %s. Will not continue" % local_branch]
        messages.append("Contact Shawn Dawson for help")
        messages.append("")
        for line in git_status_lines: messages.append(line)
        error_and_exit(-1, messages)

    # the git pull puts messages in err. So catenate out and err strings.
    code, out, err = runcommand_die_on_err("git pull --dry-run", False);
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
        messages.append("Contact Shawn Dawson for help")
        messages.append("")
        for line in git_pull_dry_run_lines: messages.append(line)
        error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # At this point, the local branch should be in synch with the remote repo.
    # So let us continue.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version ' % (majorToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    fileMajor = words[len(words) -1]

    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version ' % (minorToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    fileMinor = words[len(words) -1]

    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version ' % (patchToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    filePatch = words[len(words) -1]

    expectedMajorAsInteger = int(fileMajor)
    expectedMinorAsInteger = int(fileMinor)
    expectedPatchAsInteger = int(filePatch) + 1
    
    # -------------------------------------------------------------------------
    # If -v was given, take the major.minor.patch version from the user
    # command line.  If not, then create it based on the current version
    # information in the repo version file.
    # -------------------------------------------------------------------------
    if args.version is not None:
    
        words = args.version.split('.')     # Split the version into major and minor
    
        if len(words) != 3:
            messages = ["version '%s' is invalid" % args.version]
            messages.append("Must major_num.minor_num.patch_num string such as '5.18.1'")
            error_and_exit(-1, messages)
    
        branchMajor = words[0]
        branchMinor = words[1]
        branchPatch = words[2]
    
        if not re.match(r'^[0-9]+$', branchMajor) or not re.match(r'^[0-9]+$', branchMinor) or not re.match(r'^[0-9]+$', branchPatch):
            messages = ["version '%s' is invalid" % args.version]
            messages.append("Must major_num.minor_num.patch_num string such as '5.18.1'")
            error_and_exit(-1, messages)
    else:
        branchMajor = fileMajor
        branchMinor = fileMinor
        tempint     = int(filePatch) + 1
        branchPatch = str(tempint)

    # -------------------------------------------------------------------------
    # Warnings and error checks on the proposed version numbers
    # check the major number.
    # -------------------------------------------------------------------------
    if int(branchMajor) != int(fileMajor):
        # We can never decrease the major number
        if int(branchMajor) < int(fileMajor):
            messages = ["Current  version is %s.%s.%s" % (fileMajor, fileMinor, filePatch)]
            messages.append("Proposed version is %s.%s.%s" % (branchMajor, branchMinor, branchPatch))
            messages.append("Proposed major version %s is invalid, it must be >= %s" % (branchMajor, fileMajor))
            error_and_exit(-1, messages)
        # else branchMajor is > fileMajor
        # We can increase the major branch number only on the master branch.
        # We can not do this on a release branch.
        # Still, warn the user that this will be happening so they are alert to the change.
        else:
            if local_branch_type == "master":
                messages = ["You have requested to bump the version number from %s.%s.%s to %s.%s.%s" % (fileMajor, fileMinor, filePatch, branchMajor, branchMinor, branchPatch)]
                messages.append("Expected major version is %s" % fileMajor)
                messages.append("One is allowed to bump the master number on the %s branch" % local_branch_type)
                messages.append("However ... Carefully inspect the versions before continuing")
                warning_but_continue(messages)
                # When we bump the major version on the master branch, we expect start at patch level 1
                expectedMinorAsInteger = 1
            else:
                messages = ["You have requested to bump the version number from %s.%s.%s to %s.%s.%s" % (fileMajor, fileMinor, filePatch, branchMajor, branchMinor, branchPatch)]
                messages.append("One is not allowed to bump the major number on a %s branch" % local_branch_type)
                error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Warnings and error checks on the proposed version numbers
    # check the minor number.
    # -------------------------------------------------------------------------
    if int(branchMinor) != expectedMinorAsInteger:
        # We can never decrease the minor number
        if int(branchMinor) < expectedMinorAsInteger:
            messages = ["Current  version is %s.%s.%s" % (fileMajor, fileMinor, filePatch)]
            messages.append("Proposed version is %s.%s.%s" % (branchMajor, branchMinor, branchPatch))
            messages.append("Proposed minor version %s is invalid, it must be >= %s" % (branchMinor, expectedMinorAsInteger))
            error_and_exit(-1, messages)
        # else branchMinor is > expectedMinorAsInteger
        # We can increase the minor branch number only on the master branch.
        # We can not do this on a release branch.
        # Still, warn the user that this will be happening so they are alert to the change.
        else:
            if local_branch_type == "master":
                # If bumping the minor number, it must be an odd number, as even numbers are reserved for release branches.
                if int(branchMinor) % 2 == 0:
                    messages = ["Current  version is %s.%s.%s" % (fileMajor, fileMinor, filePatch)]
                    messages.append("Proposed version is %s.%s.%s" % (branchMajor, branchMinor, branchPatch))
                    messages.append("Proposed minor version %s is invalid" % (branchMinor))
                    messages.append("%s branch must have an an odd minor number" % (local_branch_type))
                    error_and_exit(-1, messages)
                else:
                    messages = ["You have requested to bump the version number from %s.%s.%s to %s.%s.%s" % (fileMajor, fileMinor, filePatch, branchMajor, branchMinor, branchPatch)]
                    messages.append("Expected minor version is %i" % expectedMinorAsInteger)
                    messages.append("One is allowed to bump the minor number on the %s branch" % local_branch_type)
                    messages.append("However ... Carefully inspect the versions before continuing")
                    warning_but_continue(messages)
            else:
                messages = ["You have requested to bump the version number from %s.%s.%s to %s.%s.%s" % (fileMajor, fileMinor, filePatch, branchMajor, branchMinor, branchPatch)]
                messages.append("One is not allowed to bump the minor number on a %s branch" % local_branch_type)
                error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Warnings and error checks on the proposed version numbers
    # check the patch number.
    # -------------------------------------------------------------------------
    if int(branchPatch) != int(expectedPatchAsInteger):
        # We can never decrease the patch number
        if int(branchPatch) < expectedPatchAsInteger:
            messages = ["Current  version is %s.%s.%s" % (fileMajor, fileMinor, filePatch)]
            messages.append("Proposed version is %s.%s.%s" % (branchMajor, branchMinor, branchPatch))
            messages.append("Proposed patch version %s is invalid, it must be >= %s" % (branchPatch, expectedPatchAsInteger))
            error_and_exit(-1, messages)
        # else branchPatch is > expectedPatchAsInteger
        # Warn the user that this will be happening so they are alert to the change.
        else:
            messages = ["You have requested to bump the version number from %s.%s.%s to %s.%s.%s" % (fileMajor, fileMinor, filePatch, branchMajor, branchMinor, branchPatch)]
            messages.append("Expected patch version is %i" % expectedPatchAsInteger)
            messages.append("One is allowed to bump the patch number")
            messages.append("However ... Carefully inspect the versions before continuing")
            warning_but_continue(messages)

    # -------------------------------------------------------------------------
    # Tell user what we are going to do and prompt y/n to accept.
    # -------------------------------------------------------------------------
    branchTag = "%s.%s.%s" % (branchMajor, branchMinor, branchPatch)
    print("")
    print("Current %s version is      %s.%s.%s" % (local_branch_type, fileMajor, fileMinor, filePatch))
    print("New     %s version will be %s.%s.%s and tag %s applied" % (local_branch_type, branchMajor, branchMinor, branchPatch, branchTag))

    # -------------------------------------------------------------------------
    # Now, verify that the proposed tags do not already exist on the
    # remote repo or the local repo.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err("git ls-remote --tags origin", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')
    for line in git_status_lines:
        if branchTag in line:
            messages     = ["Found remote tag : %s" % line]
            messages.append("Proposed branch tag %s is invalid" % branchTag)
            error_and_exit(-1, messages)

    code, out, err = runcommand_die_on_err("git tag", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')
    for line in git_status_lines:
        if branchTag in line:
            messages     = ["Found local tag : %s" % line]
            messages.append("Proposed branch tag %s is invalid" % branchTag)
            error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Prompt y/n to accept.
    # -------------------------------------------------------------------------
    question = "Shall we commit and push this change to %s branch" % local_branch
    answer = yes_or_no(question, args.yes)
    if answer == False:
        print("You're the boss. Cancelling the branching.")
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Now do the commands needed to create the release branch locally
    # the Bit Bucket repo and set it's origin correctly
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('sed -i \'s/MAJOR.*$/MAJOR %s/\'  %s'           % (branchMajor, repoVersionFile))
    code, out, err = runcommand_die_on_err('sed -i \'s/MINOR.*$/MINOR %s/\'  %s'           % (branchMinor, repoVersionFile))
    code, out, err = runcommand_die_on_err('sed -i \'s/PATCHLEVEL.*$/PATCHLEVEL %s/\'  %s' % (branchPatch, repoVersionFile))

    code, out, err = runcommand_die_on_err('git commit -m "Update version from %s.%s.%s to %s on %s branch" %s' % (fileMajor, fileMinor, filePatch, branchTag, local_branch, repoVersionFile) )
    code, out, err = runcommand_die_on_err('git tag %s %s' % (branchTag, local_branch) )
    code, out, err = runcommand_die_on_err('git push')
    code, out, err = runcommand_die_on_err('git push --tags')

# ----------------------------------------------------------------------------------------------------------------------
# end of file
# ----------------------------------------------------------------------------------------------------------------------

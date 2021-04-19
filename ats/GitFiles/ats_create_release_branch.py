#!/usr/bin/env python3

import os, sys, re, subprocess
import argparse

# ----------------------------------------------------------------------------------------------------------------------
# This script is used to create a release branch
#
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# Simple support routines
# ----------------------------------------------------------------------------------------------------------------------
def error_and_exit(code, messages):
    print("Error: ------------------------------------------------------------------------")
    print("Error:         C R E A T E   R E L E A S E   B R A N C H   A B E N D")
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
    if echoCmd == True:
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
    parser = argparse.ArgumentParser(description='Script to create a release branch for the project')

    parser.add_argument('-v', '--version',
                        help='OPTIONAL: Major.Minor release number such as 5.18')

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
    # This script is restricted to be run by certain users.
    # -------------------------------------------------------------------------
    user = (os.popen('whoami').read()).rstrip()

    if not user == 'dawson':
        messages = ["This script restricted to user by dawson"]
        messages.append("Contact Shawn Dawson for help")
        error_and_exit(-1, messages)
    
    # -------------------------------------------------------------------------
    # Determine the remote repo.
    # Determine the branch.
    # Verify the version header file exists.
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

    if local_branch_type != "master":
        messages = ["This script restricted to only operate within a clone of the 'master' branch"]
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
    code, out, err = runcommand_die_on_err("git status --porcelain");
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')

    if len(git_status_lines) == 1 and git_status_lines[0] == '':
        print("Info: local clone looks clean ... continuing")
    else:
        messages = ["Unsure of status of local branch %s. Will not continue" % local_branch]
        messages.append("Contact Shawn Dawson for help")
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
        messages.append("Contact Shawn Dawson for help")
        messages.append("")
        for line in git_pull_dry_run_lines: messages.append(line)
        error_and_exit(-1, messages)
    
    # -------------------------------------------------------------------------
    # At this point, the local branch should be in synch with the remote repo.
    # So let us continue.
    # Grok the current version information from the header files
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version' % (majorToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    fileMajor = words[len(words) -1]
    
    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version' % (minorToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    fileMinor = words[len(words) -1]
    
    code, out, err = runcommand_die_on_err('grep %s %s | grep -v version' % (patchToken, repoVersionFile), False);
    out1 = out.rstrip()
    words = out1.split()
    filePatch = words[len(words) -1]
    
    # -------------------------------------------------------------------------
    # If -v was given, take the major.minor branch version from the user
    # command line.  If not, then create it based on the current version
    # information in the repo version file.
    # -------------------------------------------------------------------------
    if args.version is not None:
    
        words = args.version.split('.')     # Split the version into major and minor
    
        if len(words) != 2:
            messages = ["version '%s' is invalid" % args.version]
            messages.append("Must major_num.minor_num string such as '5.18'")
            messages.append("Exiting without creating version branch")
            error_and_exit(-1, messages)
    
        branchMajor = words[0]
        branchMinor = words[1]
    
        if not re.match(r'^[0-9]+$', branchMajor) or not re.match(r'^[0-9]+$', branchMinor):
            messages = ["version '%s' is invalid" % args.version]
            messages.append("Must major_num.minor_num string such as '5.18'")
            messages.append("Exiting without creating version branch")
            error_and_exit(-1, messages)
    else:
        branchMajor = fileMajor
        tempint            = int(fileMinor) + 1
        branchMinor = str(tempint)
    
    # -------------------------------------------------------------------------
    # We will also bump and tag the master (trunk) version to be 1 more than the branch 
    # version, so calculate this number now.
    # -------------------------------------------------------------------------
    branchMinorAsInteger = int(branchMinor)
    masterMinorAsInteger = branchMinorAsInteger + 1
    masterMajor          = branchMajor
    masterMinor          = str(masterMinorAsInteger)
    branchMajorMinor     = "%s.%s" % (branchMajor, branchMinor)
    
    expectedMinorAsInteger = int(fileMinor) + 1
    
    # -------------------------------------------------------------------------
    # Warnings and error checks on the proposed version numbers
    # -------------------------------------------------------------------------
    if int(fileMajor) != int(branchMajor):
        if int(branchMajor) < int(fileMajor):
            messages = ["Current version is %s.%s.%s" % (fileMajor, fileMinor, filePatch)]
            messages.append("-v specified major version %s is invalid, it must be >= %s" % (branchMajor, fileMajor))
            error_and_exit(-1, messages)
        else: # branchMajor is > fileMajor)
            messages = ["You have requested to bump the major number from %s to %s" % (fileMajor, branchMajor)]
            messages.append("Carefully inspect the versions below before continuing")
            warning_but_continue(messages)
    
            # When we bump the major version, we expect create a minor version of 0 (such as 6.0) for the release branch
            expectedMinorAsInteger = 0
     
    if expectedMinorAsInteger != int(branchMinor):
        if int(branchMinor) < expectedMinorAsInteger:
            messages = ["-v specified minor version %s is invalid. It must be >= %s" % (branchMinor, expectedMinorAsInteger)]
            error_and_exit(-1, messages)
        else:   # branchMinor is > expectedMinorAsInteger
            messages = ["You have requested to bump the minor number to %s (expected it to be %s)" % (branchMinor, str(expectedMinorAsInteger))]
            messages.append("Carefully inspect the versions below before continuing")
            warning_but_continue(messages)
    
    branchTag = "%s.%s.%s" % (branchMajor, branchMinor, "0")
    masterTag = "%s.%s.%s" % (masterMajor, masterMinor, "0")
    
    if int(branchMinor) % 2 == 1:
        messages = ["Release branches must have an even-numbered minor number"]
        messages.append("Proposed branch version %s is invalid" % branchTag)
        error_and_exit(-1, messages)
    
    if int(masterMinor) % 2 == 0:
        messages = ["Master (trunk) versions must have an odd-numbered minor number"]
        messages.append("Proposed master version %s is invalid" % masterTag)
        error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Tell user what we are going 
    # -------------------------------------------------------------------------
    print ("")
    print("Info: Current master version is .... %s.%s.%s" % (fileMajor, fileMinor, filePatch))
    print("Info: Release branch version will be %s" % branchTag) 
    print("Info: Next    master version will be %s" % masterTag)

    # -------------------------------------------------------------------------
    # Now, verify that the proposed branch does not already exist on the
    # remote repo or the local repo.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err("git branch -r", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')
    for line in git_status_lines: 
        if branchMajorMinor in line:
            messages     = ["Found remote branch : %s" % line]
            messages.append("Proposed branch %s is invalid" % branchMajorMinor)
            error_and_exit(-1, messages)

    code, out, err = runcommand_die_on_err("git branch", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')
    for line in git_status_lines:
        if branchMajorMinor in line:
            messageTagts     = ["Found local branch : %s" % line]
            messages.append("Proposed branch %s is invalid" % branchMajorMinor)
            error_and_exit(-1, messages)

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
        if masterTag in line:
            messages     = ["Found remote tag : %s" % line]
            messages.append("Proposed master tag %s is invalid" % masterTag)
            error_and_exit(-1, messages)

    code, out, err = runcommand_die_on_err("git tag", False);
    git_status = out.rstrip()
    git_status_lines = git_status.split('\n')
    for line in git_status_lines:
        if branchTag in line:
            messages     = ["Found local tag : %s" % line]
            messages.append("Proposed branch tag %s is invalid" % branchTag)
            error_and_exit(-1, messages)
        if masterTag in line:
            messages     = ["Found local tag : %s" % line]
            messages.append("Proposed master tag %s is invalid" % masterTag)
            error_and_exit(-1, messages)

    # -------------------------------------------------------------------------
    # Tell user what we are going to do and prompt y/n to accept.
    # -------------------------------------------------------------------------
    branch_name = '%s/%s' % ("release", branchMajorMinor)
    question = "Shall we continue to make the above happen for repo %s " % (remote_repo)
    answer = yes_or_no(question, args.yes)
    if answer == False:
        print("You're the boss. Cancelling the branching.")
        sys.exit(0)
    
    # -------------------------------------------------------------------------
    # Now do the commands needed to create the release branch locally
    # the Bit Bucket repo and set it's origin correctly
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('git checkout -b %s' % branch_name);
    code, out, err = runcommand_die_on_err('sed -i \'s/MINOR.*$/MINOR %s/\'  %s' % (branchMinor, repoVersionFile));
    code, out, err = runcommand_die_on_err('sed -i \'s/PATCHLEVEL.*$/PATCHLEVEL 0/\'  %s' % (repoVersionFile));
    code, out, err = runcommand_die_on_err('git commit -m "Update version to %s on %s branch" %s' % (branchTag, branch_name, repoVersionFile) );
    code, out, err = runcommand_die_on_err('git tag %s %s' % (branchTag, branch_name) );
    
    # -------------------------------------------------------------------------
    # Ask user if we want to push this new branch to the remote bit bucket repo
    # If no, then we are done.  If yes, then do the push.
    # -------------------------------------------------------------------------
    #question = "Do you want to push these local updates to the BitBucket repo" 
    #answer = yes_or_no(question, args.yes)
    #if answer == False:
    #    print("Exiting without pushing local updates to the Bitbucket repo")
    #    sys.exit(0)
    
    code, out, err = runcommand_die_on_err('git push --set-upstream origin %s' % branch_name);
    code, out, err = runcommand_die_on_err('git push --tags');
    
    # -------------------------------------------------------------------------
    # Ask the user if we should now bump and tag the 'master' branch.
    # We are committed at this point, as we have created and tagged the release
    # branch. So forge head and update the master branch now.
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('git checkout master');
    code, out, err = runcommand_die_on_err('git pull');
    code, out, err = runcommand_die_on_err('sed -i \'s/MINOR.*$/MINOR %s/\'  %s' % (masterMinor, repoVersionFile));
    code, out, err = runcommand_die_on_err('sed -i \'s/PATCHLEVEL.*$/PATCHLEVEL 0/\'  %s' % (repoVersionFile));
    code, out, err = runcommand_die_on_err('git commit -m "Update version to %s on master branch" %s' % (masterTag, repoVersionFile) );
    code, out, err = runcommand_die_on_err('git tag %s %s' % (masterTag, "master") );
    code, out, err = runcommand_die_on_err('git push');
    code, out, err = runcommand_die_on_err('git push --tags');

    # -------------------------------------------------------------------------
    # At the end of this script, leave the user in the newly created branch
    # -------------------------------------------------------------------------
    code, out, err = runcommand_die_on_err('git checkout %s' % branch_name);


# ----------------------------------------------------------------------------------------------------------------------
# end of file
# ----------------------------------------------------------------------------------------------------------------------


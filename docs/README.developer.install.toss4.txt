
export PATH=${PATH}:/usr/gapps/ats/scripts

Set this as appropriate for you

    export CLONE_SPACE="/usr/workspace/wsrzd"
    export CLONE_SPACE="/usr/workspace/wsb"    
    
# Install ATS from GitHub

    # Install an ATS version of python based on the public version.

ls -la /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
rm -rf /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
module load python/3.9.12
python3 -m virtualenv --system-site-packages --python=python3.9 /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
export PATH=/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin:$PATH

    # these lines are only necessary if you have not yet cloned the ATS repo.
    # If you have, you may want to do a 'git clean' to cleanup prior installs from other systems.

git clone git@github.com:LLNL/ATS.git ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
git branch feature/${USER}/mydevbranch
git push --set-upstream origin feature/${USER}/mydevbranch 
git checkout feature/${USER}/mydevbranch

    # Install of ATS
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin/python -m pip install `pwd`
set.permissions.nogroup.write /usr/gapps/ats/${SYS_TYPE}/7.0.${USER} atsb

    # Install of ATS extensions from GitLAB
git clone ssh://git@czgitlab.llnl.gov:7999/dawson/atsllnl.git ${CLONE_SPACE}/${USER}/Git-ATS-GitLab-${USER}
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitLab-${USER}
./scripts/update-version-llnl.x
/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin/python -m pip install `pwd` 
./setup.fix 3.9 ${USER} 
set.permissions.nogroup.write /usr/gapps/ats/${SYS_TYPE}/7.0.${USER} atsb

---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------

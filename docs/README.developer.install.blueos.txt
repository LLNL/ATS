
export PATH=${PATH}:/usr/gapps/ats/scripts

Set this as appropriate for you

    export CLONE_SPACE="/usr/workspace/wsrzd"
    export CLONE_SPACE="/usr/workspace/wsb"

    // install python
ls -la /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
rm -rf /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
module load python/3.8.2
python3 -m virtualenv --system-site-packages --python=python3.8 /usr/gapps/ats/${SYS_TYPE}/7.0.${USER}
export PATH=/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin:$PATH

    // lines not necessary if you already have a clone
git clone git@github.com:LLNL/ATS.git ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
git branch feature/${USER}/mydevbranch
git push --set-upstream origin feature/${USER}/mydevbranch 
git checkout feature/${USER}/mydevbranch

    // install ats
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitHub-${USER}
/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin/python -m pip install `pwd`
set.permissions.noworld /usr/gapps/ats/${SYS_TYPE}/7.0.${USER} atsb

    # Install of ATS extensions from GitLAB
git clone ssh://git@czgitlab.llnl.gov:7999/dawson/atsllnl.git ${CLONE_SPACE}/${USER}/Git-ATS-GitLab-${USER}
cd ${CLONE_SPACE}/${USER}/Git-ATS-GitLab-${USER}
./scripts/update-version-llnl.x
./scripts/update-version-llnl.x
/usr/gapps/ats/${SYS_TYPE}/7.0.${USER}/bin/python -m pip install `pwd` 
./setup.fix 3.8 ${USER} 
set.permissions.nogroup.write /usr/gapps/ats/${SYS_TYPE}/7.0.${USER} atsb

---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------

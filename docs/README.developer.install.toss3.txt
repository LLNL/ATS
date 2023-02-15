
export PATH=${PATH}:/usr/gapps/ats/scripts

# Install ATS from GitHub

    # Install an ATS version of python based on the public version.
ls -la /usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}
rm -rf /usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}
module load python/3.8.2
python3 -m virtualenv --system-site-packages --python=python3.8 /usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}
export PATH=/usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}/bin:$PATH

    # these lines are only necessary if you have not yet cloned the ATS repo.
    # If you have, you may want to do a 'git clean' to cleanup prior installs from other systems.
git clone git@github.com:LLNL/ATS.git /usr/workspace/wsrzd/${USER}/Git-ATS-GitHub-${USER}
cd /usr/workspace/wsrzd/${USER}/Git-ATS-GitHub-${USER}
git branch feature/${USER}/mydevbranch
git push --set-upstream origin feature/${USER}/mydevbranch
/usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}/bin/python -m pip install `pwd`
git checkout feature/${USER}/mydevbranch

    # Install of ATS
cd /usr/workspace/wsrzd/${USER}/Git-ATS-GitHub-${USER}
/usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}/bin/python -m pip install `pwd`
set.permissions.nogroup.write /usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER} atsb

    # Install of ATS extensions from GitLAB
cd /g/g16/${USER}/wci/Git-ATS-GitLab-${USER}
./scripts/update-version-llnl.x
/usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER}/bin/python -m pip install `pwd` 
./setup.fix 3.8 ${USER} 
set.permissions.nogroup.write /usr/gapps/ats/toss_3_x86_64_ib/7.0.${USER} atsb



---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------

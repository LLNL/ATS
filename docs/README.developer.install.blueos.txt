export PATH=${PATH}:/usr/gapps/ats/scripts

    // install python
ls -la /usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}
rm -rf /usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}
module load python/3.8.2
python3 -m virtualenv --system-site-packages --python=python3.8 /usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}
export PATH=/usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}/bin:$PATH

    // lines not necessary if you already have a clone
git clone git@github.com:LLNL/ATS.git /usr/workspace/wsrzd/${USER}/Git-ATS-GitHub-${USER}
cd /usr/workspace/wsrzd/${USER}/Git-ATS-GitHub-${USER}
git branch feature/${USER}/mydevbranch
git push --set-upstream origin feature/dawson/mydevbranch 
git checkout feature/${USER}/mydevbranch

    // install ats
/usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}/bin/python -m pip install `pwd`
set.permissions.noworld /usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER} atsb

    # Install of ATS extensions from GitLAB
cd /g/g16/dawson/wci/Git-ATS-GitLab-${USER}
./scripts/update-version-llnl.x
/usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER}/bin/python -m pip install `pwd` 
./setup.fix 3.8 ${USER} 
set.permissions.nogroup.write /usr/gapps/ats/blueos_3_ppc64le_ib_p9/7.0.${USER} atsb

---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------

2022 May 24

Testing ATS with Kripke.

1) Retrieve Kripke from github from this location.


https://github.com/LLNL/Kripke/releases

This testing was based on the tarfile kripke-v1.2.5-20e9ea9.tar.gz from the above location.

1) Build Kripke in this directory (test/Kripke)

pushd .
tar -xvzf kripke-v1.2.5-20e9ea9.tar.gz
cd kripke-v1.2.5-20e9ea9
mkdir build
cd build
cmake .. -C../host-configs/llnl-toss3-gcc8.1.cmake -DCMAKE_BUILD_TYPE=Release
make -j 8
popd


2) Run Kripke under ATS.  Some examples are:


/usr/apps/ats/7.0.4/bin/atslite1.py
/usr/apps/ats/7.0.4/bin/atslite1.py --postrunScript=`pwd`/postrun.py
/usr/apps/ats/7.0.4/bin/atslite1.py --postrunScript=`pwd`/postrun.py --prerunScript=`pwd`/prerun.py


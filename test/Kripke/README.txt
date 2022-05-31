2022 May 24

Testing ATS with Kripke.

1) Retrieve Kripke from github from this location.

https://github.com/LLNL/Kripke/releases

This testing was based on the tarfile kripke-v1.2.6-1-g0d24be5.tar.gz from the above location.

<<< -------------------- >>> 
<<<  TOSS BUILD AND TEST >>>
<<< -------------------- >>> 

1) Build Kripke in this directory (test/Kripke)

pushd .
tar -xvzf kripke-v1.2.6-1-g0d24be5.tar.gz
cd kripke-v1.2.6-1-g0d24be5
mkdir build
cd build
cmake .. -C../host-configs/llnl-toss3-gcc8.1.cmake -DCMAKE_BUILD_TYPE=Release
make -j 8
popd


2) Run Kripke under ATS.  Some examples are:

atslite1
atslite1 --postrunScript=`pwd`/postrun.py
atslite1 --postrunScript=`pwd`/postrun.py --prerunScript=`pwd`/prerun.py

<<< ------------------------------ >>> 
<<<  BLUEOS BUILD AND TEST NON GPU  >>>
<<< ------------------------------ >>> 

cd kripke-v1.2.6-1-g0d24be5
rm -rf build
mkdir build
cd build
cmake .. -C../host-configs/llnl-blueos-clang.cmake -DCMAKE_BUILD_TYPE=Release
make -j 8
cd ../..


2) Run Kripke under ATS.  Some examples are:

atslite1 --smpi_off
atslite1 --smpi_off --postrunScript=`pwd`/postrun.py
atslite1 --smpi_off --postrunScript=`pwd`/postrun.py --prerunScript=`pwd`/prerun.py




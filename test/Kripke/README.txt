2022 May 24

Testing ATS with Kripke.

Kripke is open source and is on GitHub at this location:

    https://github.com/LLNL/Kripke/releases

This testing was based on the tarfile kripke-v1.2.5-20e9ea9.tar.gz from here:

    https://github.com/LLNL/Kripke/releases/download/v1.2.5/kripke-v1.2.5-20e9ea9.tar.gz


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


atslite1.py
atslite1.py --postrunScript=`pwd`/postrun.py
atslite1.py --postrunScript=`pwd`/postrun.py --prerunScript=`pwd`/prerun.py

===== BlueOS Lassen Testing ==============================================

pushd .
tar -xvzf kripke-v1.2.5-20e9ea9.tar.gz
cd kripke-v1.2.5-20e9ea9
mkdir build
cd build
cmake .. -C../host-configs/llnl-blueos-V100-nvcc-clang.cmake  -DCMAKE_BUILD_TYPE=Release
make -j 8
popd

atslite1  --lrun --smpi_off --verbose


===== Special Whippet Build and Run Notes as of 2022 October 12 ======

LD_LIBRARY_PATH=/usr/lib64/flux

Use this cmake line when configuring and building on whippet:

    cmake .. -C../host-configs/llnl-toss4-intel-classic.cmake  -DCMAKE_BUILD_TYPE=Release
or
    cmake .. -C../host-configs/llnl-toss4-intel-2022.1.0.cmake  -DCMAKE_BUILD_TYPE=Release

Run Kripke using atsflux 

    ./create_test_ats.py
    atsflux --flux test.ats --verbose


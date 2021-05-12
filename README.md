# ATS

## Description

ATS is an Automated Test System. It is used to implement regression testing across a variety of HPC platforms. 

## Getting Started

These are the Python 2 based 'old style' install instructions.  They depend on one having a Python 2 installed in user writable location, and then ATS is installed into that location.  This python should include installs of numpy, matplotlib, and scipy which are used by ATS. You can contact dawson6@llnl.gov if one needs help with this Python install.

Once one has this done, ATS is installed like so:

    git clone git@github.com:LLNL/ATS.git
    cd ATS/ats
    /path/to/your/writable/python setup-py2.py install;

When we finish the port to Python 3, a new  installation method will be used, which does not depend on a user building Python.

## Getting Involved

Contact the ATS project lead dawson6@llnl.gov

## Contributing 

Refer to file [Contributing](CONTRIBUTING.md)


## Release

ATS is licensed under the BSD 3-Clause license, (BSD-3-Clause or
https://opensource.org/licenses/BSD-3-Clause).

Refer to [LICENSE](LICENSE)

LLNL-CODE-820679


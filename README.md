[![Documentation Status](https://readthedocs.org/projects/ats/badge/?version=main)](https://ats.readthedocs.io/en/main/?badge=main)

# ATS

## Description

ATS is an Automated Test System. It is used to implement regression testing
across a variety of HPC platforms. 

## Getting Started

ATS usage and expectations vary among its user base. This also applies to how
ATS is installed. Below are a few variations that users may find helpful.

For more information, please check our [documentation](https://ats.readthedocs.io).

#### Sample install, modify for your project or personal usage. 

An  install really means a Python executable with ATS modules discoverable in its python path. 
Useful for multiple different projects in a shared environment.

Example installation:

```
# Load a python 3.8 module, or otherwise put python 3.8 in your path
module load python/3.8.2

# Create a fresh Python 3.8 (or higher) executable to be shared.
python3 -m virtualenv --system-site-packages --python=python3.8 /location/of/your/new/install

# Clone ATS
git clone git@github.com:LLNL/ATS.git <CLONE_PATH>

# pip install cloned ATS into fresh shared Python 3.8 (or higher) executable.
/location/of/your/new/install/bin/python -m pip install <CLONE_PATH>/
```

## Getting Involved

Contact the ATS project lead dawson6@llnl.gov

## Contributing 

Refer to file [Contributing](CONTRIBUTING.md)


## Release

ATS is licensed under the BSD 3-Clause license, (BSD-3-Clause or
https://opensource.org/licenses/BSD-3-Clause).

Refer to [LICENSE](LICENSE)

LLNL-CODE-820679


---------------------------------------------------------------------------------------------------
COPYRIGHT
---------------------------------------------------------------------------------------------------

Copyright (c) 2021
Lawrence Livermore National Security, LLC

This work was performed under the auspices of the U.S. Department of Energy by 
Lawrence Livermore National Laboratory under Contract DE-AC52-07NA27344.

DISCLAIMER
----------
This document was prepared as an account of work sponsored by an agency of the United States 
government. Neither the United States government nor Lawrence Livermore National Security, 
LLC, nor any of their employees makes any warranty, expressed or implied, or assumes any 
legal liability or responsibility for the accuracy, completeness, or usefulness of any 
information, apparatus, product, or process disclosed, or represents that its use would not 
infringe privately owned rights. Reference herein to any specific commercial product, 
process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily 
constitute or imply its endorsement, recommendation, or favoring by the United States government 
or Lawrence Livermore National Security, LLC. The views and opinions of authors expressed 
herein do not necessarily state or reflect those of the United States government or 
Lawrence Livermore National Security, LLC, and shall not be used for advertising or 
product endorsement purposes.

All files in this directory and below are subject to this copyright.

---------------------------------------------------------------------------------------------------
Site installation of ATS 
---------------------------------------------------------------------------------------------------

If you have a Python distribution you would like to install the ATS into as a site package, use:

cd <your_git_clone>;
/path/to/your/python setup.py install;

cd <your_git_clone>/LC;
/path/to/your/python setup.py install;

After installation, atsb is the Unix executable. On Windows, you have to 
make a shortcut that executes python atsb ... <rest of arguments>.

---------------------------------------------------------------------------------------------------
Local installation of ATS
---------------------------------------------------------------------------------------------------
Refer to the sandbox repo for installing ATS along with an ATS specific python.

---------------------------------------------------------------------------------------------------
Documentation
---------------------------------------------------------------------------------------------------
To install the documentation builder Sphinx into your python, use 
easy_install -U Sphinx.

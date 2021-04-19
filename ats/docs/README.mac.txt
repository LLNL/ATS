ATS Installation on a Mac
=========================

Assume the ATS source is contained in a directory named "~/ats_scr".


If you are an admin and want to install ATS in an existing python installation
---------------------------------------------------------------------------
    cd ~/ats_scr
    python setup.py install



If you are an admin and want to install ATS without disturbing an existing 
python installation.
---------------------------------------------------------------------------

Install pip globally, if it not already installed.

    sudo easy_install pip

Test that it is installed.

    rehash
    pip


Install virtualenv globally, if it not already installed.

    sudo pip install virtualenv

Test that it is installed.

    rehash
    virtualenv


Create a virtual Python environment. Assume the directory in which to install 
it is named "~/Python_venv".

    virtualenv ~/Python_venv


There are two ways to install ATS in the virtual environment.

    1. Activate it and work within it. Use "activate" if you are using a bash 
       environment or "activate.csh" if you are using a csh environment:

        source ~/Python_venv/bin/activate
        pip install numpy
        pip install nose
        cd ~/ats_scr
        python setup.py install
        deactivate


    2. Point directly to the virtual python, or set the PATH environment 
       variable.

        cd ~/ats_scr
        ~/Python_venv/bin/python setup.py install




If you are not an admin and want to install ATS in a private python area.
---------------------------------------------------------------------------

You will need to install a couple of pieces of software in a non-public
directory. Assume it is named "~/bin".

Add this directory to your PATH and PYTHONPATH environment variables, if not
already there.

Install pip, if it not already installed globally or privately.

    easy_install --install-dir ~/bin pip

Test that it is installed.

    rehash
    pip


Install virtualenv, if it not already installed globally or privately.

    pip install --target ~/bin virtualenv

Test that it is installed.

    rehash
    python ~/bin/virtualenv.py


Create a virtual Python environment. Assume the directory in which to install 
it is named "~/Python_venv".

    python ~/bin/virtualenv.py ~/Python_venv


There are two ways to install ATS in the virtual environment.

    1. Activate it and work within it. Use "activate" if you are using a bash 
       environment or "activate.csh" if you are using a csh environment:

        source ~/Python_venv/bin/activate
        pip install numpy
        pip install nose
        cd ~/ats_scr
        python setup.py install
        deactivate


    2. Point directly to the virtual python, or set the PATH environment 
       variable.

        cd ~/ats_scr
        ~/Python_venv/bin/python setup.py install


from __future__ import print_function

import sys, os, shutil, glob, stat
from setuptools import find_packages, setup
from modulefinder import ModuleFinder

def get_version():
    finder = ModuleFinder()
    finder.run_script('version.py')
    from version import version as version_text
    return version_text


setup(
    name="ats",
    author="Shawn A. Dawson",
    author_email="dawson6@llnl.gov",
    url="https://github.com/LLNL/ATS",
    version=get_version(),
    description="Automated Testing System",
    install_requires=['numpy <= 1.16.5'],
    package_dir={'': 'src'},
    packages=find_packages(
        where='src',
        exclude=['ats.charts', 'ats.database', 'LC']
    ),
    data_files=[
        ('atsASC/Visit/visit_testing/report_templates/css',       glob.glob('src/atsASC/Visit/visit_testing/report_templates/js/*')),
        ('atsASC/Visit/visit_testing/report_templates',           glob.glob('src/atsASC/Visit/visit_testing/report_templates/*.html')),
        ('atsASC/Visit/visit_testing',                            glob.glob('src/atsASC/Visit/visit_testing/*.pnm')),
        ('atsASC/Visit/visit_testing',                            glob.glob('src/atsASC/Visit/visit_testing/*.txt')),
        ('atsASC/Visit/Example/baseline/category/example_script', glob.glob('src/atsASC/Visit/Example/baseline/category/example_script/*')),
        ('atsASC/Visit/Example/data',                             glob.glob('src/atsASC/Visit/Example/data/*')),
        ('atsASC/Visit/Example/tests/category',                   glob.glob('src/atsASC/Visit/Example/tests/category/*')),
        ('atsASC/HelloATS',                                       glob.glob('src/atsASC/HelloATS/*')),
        ('atsASC/HelloGPU',                                       glob.glob('src/atsASC/HelloGPU/*')),
    ],
    entry_points={
        'console_scripts': [
            'ats=ats.bin._ats:main',
            'ats3=ats.bin._ats3:main',
            'atslite1=ats.bin.atslite1:main',
            'atslite3=ats.bin.atslite3:main'
        ]
    },
)

print ('---------------------------------------------------------------------')
print ('               SAD FIXUP TIL DAVID CAN HELP')
print ('---------------------------------------------------------------------')

SYS_TYPE = os.environ.get("SYS_TYPE", sys.platform)
# print ('SYS_TYPE ', SYS_TYPE)


# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsASC')
the_link  = tempstr.replace('bin/python','atsASC')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)

# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsASC')
the_link  = tempstr.replace('bin/python','lib/python2.7/site-packages/atsASC')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)

# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsExtras')
the_link  = tempstr.replace('bin/python','lib/python2.7/site-packages/atsExtras')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)

# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsExtras')
the_link  = tempstr.replace('bin/python','atsExtras')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)


# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/ats')
the_link  = tempstr.replace('bin/python','lib/python2.7/site-packages/ats')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)

# Set bits on some executable py files
#the_file = "/usr/gapps/atsb/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsASC/Kripke/ats_check_log.py"
#os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/checkers/UltraCheck106.py"
# print ('the_file is ', the_file)
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/checkers/UltraCheck107.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/checkers/ValgrindCheck100.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/checkers/modules/UltraCheck.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/checkers/modules/UltraCheckBase2.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/modules/UltraCheck.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

the_file = "/usr/gapps/ats/" + SYS_TYPE + "/7.0.0/lib/python2.7/site-packages/atsASC/modules/UltraCheckBase2.py"
os.chmod(the_file, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


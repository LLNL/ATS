from __future__ import print_function
import sys, os, shutil, glob
from distutils.core import setup

if os.path.exists('build'):
    shutil.rmtree('build')

print ('---------------------------------------------------------------------')
print ('               SAD FIXUP TIL DAVID CAN HELP')
print ('---------------------------------------------------------------------')

# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
atsASC_Machines_dir  = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsMachines')
atsASC_Machines_link  = tempstr.replace('bin/python','lib/python2.7/site-packages/atsMachines')
print ('Linking  ', atsASC_Machines_link, ' -> ', atsASC_Machines_dir)
if os.path.islink(atsASC_Machines_link):
    os.unlink(atsASC_Machines_link)
os.symlink(atsASC_Machines_dir, atsASC_Machines_link)

here = os.getcwd()
machs = glob.glob(os.path.join(here, 'Machines', '*.py'))

print ('Installing into ', atsASC_Machines_dir) 
for filename in machs:
    print ('Installing', filename) 
    shutil.copy( filename, atsASC_Machines_dir )


# Create link so this looks the same as when David Bloss sets it up not compiling python2 from scratch
tempstr = sys.executable
the_dir = tempstr.replace('bin/python','lib/python2.7/site-packages/ats-7.0.0-py2.7.egg/atsMachines')
the_link  = tempstr.replace('bin/python','atsMachines')
print ('Linking  ', the_link, ' -> ', the_dir)
if os.path.islink(the_link):
    os.unlink(the_link)
os.symlink(the_dir, the_link)





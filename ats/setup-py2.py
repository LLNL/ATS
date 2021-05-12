import sys, os, shutil, glob
from distutils.core import setup
execfile('src/ats/version.py')



# -----------------------------------------------------------------------------
# write ats script
#
# -----------------------------------------------------------------------------
codename = 'ats'
f = open(codename, 'w')
driverscript = """#!%s/bin/python
import sys

try:
    import ats
except ImportError:
    print >>sys.stderr, "ats module cannot be imported; check Python path."
    print >>sys.stderr, sys.path
    raise SystemExit, 1

result = ats.manager.main()
sys.exit(result)
""" % sys.exec_prefix
print >>f, driverscript
f.close()
os.chmod(codename, 7*64 + 7*8 + 5)

# -----------------------------------------------------------------------------
# write ats3 script
# -----------------------------------------------------------------------------
codename3 = 'ats'
f = open(codename3, 'w')
driverscript = """#!%s/bin/python
import sys
import ats

ats.manager.main()

return_code = ats.manager._summary3()

sys.exit(return_code)
""" % sys.exec_prefix
print >>f, driverscript
f.close()
os.chmod(codename3, 7*64 + 7*8 + 5)

# -----------------------------------------------------------------------------
# Remove prior build
# -----------------------------------------------------------------------------
if os.path.exists('build'):
    shutil.rmtree('build')

# -----------------------------------------------------------------------------
# Install ATS
# -----------------------------------------------------------------------------
setup (name = "ats",
       author="Shawn A. Dawson",
       author_email="dawson6@llnl.gov",
       url="https://github.com/LLNL/ATS",
       version=version,
       description = "Automated Testing System",
       packages = ['ats', 
                   'ats.bin',
                   'ats.util', 
                   'atsMachines'],
       package_dir = {'ats'         : 'src/ats',
                      'ats.bin'     : 'src/ats/bin',
                      'ats.util'    : 'src/ats/util', 
                      'atsMachines' : 'src/atsMachines'},
       scripts = [codename, codename3],
       data_files = [('bin', glob.glob('src/ats/bin/atslite1.py')),
                     ('bin', glob.glob('src/ats/bin/atslite3.py')),
                     ('bin', glob.glob('ats3')),
                     ('bin', glob.glob('ats'))]
      )

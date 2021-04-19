#!/usr/apps/ats/7.0.0/bin/python

import sys
import os

sys.dont_write_bytecode = True

####################################################################################

def makeCommandLine( checker_opts, checker_files, verbose=False ):
    
  pp_clas  = checker_opts['default_args'] + ' ' + checker_opts['extra_args']

  if verbose:
    pp_clas  += ' --verbose'
    
  # Set the path to gnuplot for the UltraChecker script to use.
  if checker_opts['gnuplot']:
    gnuplot = checker_opts['gnuplot']

  elif os.environ.get('SYS_TYPE') == 'bgqos_0':
    gnuplot = '/usr/gapps/ats/ASC/bgqos_0/bin/gnuplot'

  elif os.environ.get('SYS_TYPE') == 'chaos_5_x86_64_ib':
    gnuplot = '/usr/gapps/ats/ASC/chaos_5_x86_64_ib/gnuplot-5.2.2/bin/gnuplot'

  elif os.environ.get('SYS_TYPE') == 'blueos_3_ppc64le_ib':
    gnuplot = '/usr/gapps/ats/ASC/blueos_3_ppc64le_ib/gnuplot-5.2.2/bin/gnuplot'

  elif os.environ.get('SYS_TYPE') == 'toss_3_x86_64_ib':
    gnuplot = '/usr/gapps/ats/ASC/toss_3_x86_64_ib/gnuplot-5.2.2/bin/gnuplot'

  elif os.environ.get('SYS_TYPE') == 'toss_4_x86_64_ib_cray':
    gnuplot = '/usr/bin/gnuplot'

  else:
    gnuplot = '/usr/local/bin/gnuplot'

  pp_clas  += ' --gnuplot %s' % gnuplot

  pp_clas  += " --kernel=%s" % checker_opts['kernel']

  if checker_opts['directory']:
    pp_clas += ' -d ' + checker_opts['directory']

  if checker_opts['abs_tol']:
    pp_clas += ' --abs ' + checker_opts['abs_tol']

  if checker_opts['rel_tol']:
    pp_clas += ' --rel ' + checker_opts['rel_tol']

  pp_clas += " --curvefile_baseline=%s --curvefile=%s" % ( checker_files[0],
                                                           checker_files[1])

  return pp_clas

# #################################################################################################

if __name__=="__main__":
  
  # Set path to modules under directory where script is.
  if sys.path[0]:
    script_path = sys.path[0]
    # print "DEBUG script_path is %s" % script_path
    sys.path.append( os.path.join( script_path,'modules') )

  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #if os.environ.get('SYS_TYPE') == 'bgqos_0':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #elif os.environ.get('SYS_TYPE') == 'sles_10_ppc64':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #elif os.environ.get('SYS_TYPE') == 'chaos_5_x86_64_ib':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #elif os.environ.get('SYS_TYPE') == 'chaos_5_x86_64':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #elif os.environ.get('SYS_TYPE') == 'toss_3_x86_64_ib':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  #elif os.environ.get('SYS_TYPE') == 'blueos_3_ppc64le_ib':
  #  os.environ['GDFONTPATH'] = '/usr/gapps/ats/ASC/fonts'

  from atsASC.modules.UltraCheckBase2 import UltraCheckBase2

  class UltraCheck107(UltraCheckBase2):
    def dummy(self):
      pass


  checker = UltraCheck107()

  sys.exit( checker.main() )


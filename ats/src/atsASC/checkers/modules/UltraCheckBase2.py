#!/usr/bin/env python

from six.moves import zip_longest
import os
import sys
import re
import optparse
import glob
import shutil
import numpy as np
import time
from subprocess import Popen, PIPE
from optparse   import OptionParser

from atsASC.modules.ASC_utils import listfiles

tempstr = sys.executable
print "UltraCheckBase2 Info: sys.executable = %s" % sys.executable

#
# Returns true if input string is a valid float number
#
def is_a_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
#
# Remove redundant spacing in a string 
#
def remove_space(s):
    return " ".join(s.split())

#
# Used to duplicate the 'x' val in a single point
# edit so that we can have 2 points for a curve.
# Either double the original x val, or use 1 
# if the oringal x val is 0
#
def dup_xval(number):
    if number == 0:
        return 1
    else:
        return number * 2

#
# Verify and Massage the lines in the ultra file a bit so they conform to 
# to valid x-y data curves and valid comments.
#
# Accept lines which start with '#'
# Accept lines which start with 'end'
# For other lines:
#   reject lines which do not have 2 tokens
#       This gets rid of the last single x value in 'histogram' or 'bin' type
#           'curves'
#   if a line has 2 tokens:
#       if both tokens are numbers, then accept it
#       if the 2nd token is a number, but the first is a string, then
#          change the string a sequential number and accept the converted line:
#          This changes lines such as
#               'Collided 6.0818236958e-16' to '1.0e+0  6.0818236958e-16'
#               'None     3.0536180070e-15' to '2.0e+0  3.0536180070e-15'
#          So that they will look like a curve.
#       Otherwise, reject the 2 token line
#
def verify_number_pairs(in_lines):
    assigned_number = 1
    out_lines = []
    for line in in_lines:
        if   line.startswith('#'):
            out_lines.append(line)
        elif line.startswith('end'):
            out_lines.append(line)
        else:
            tokens = line.split()
            if len(tokens) == 2:
                if is_a_number(tokens[0]) and is_a_number(tokens[1]):
                    out_lines.append(line)
                elif is_a_number(tokens[1]):
                    new_line = "%24.12e %s" % (assigned_number, tokens[1])
                    assigned_number += 1
                    out_lines.append(new_line)
                    print "Info: Converting line '%s' to '%s'" % (line, new_line)
                else:
                    print "Info: Discarding non number pair line '%s'" % line
            else:        
                print "Info: Discarding non number pair line '%s'" % line
           
    return out_lines

#
# Adjust name of curve such that it will not cause issues when used
# by gnuplot for creating file names which are valid on both Unix
# and Window systems
#
# 1) strip preceding and trailing white space.
# 2) Convert problem chars to white space
# 3) Tokenize the string on white space and join it again with 
#    '_' underscores in lieu of white space, this removes duplicate
#    white spaces first, then changes them to underscores.
#
def adjust_curve_name(in_name):
    out_name = in_name.strip()                              
    out_name = re.sub(r"[#\-()<>\[\]:.^/\\]", " ", out_name)
    out_name = "_".join(out_name.split())
    return out_name


#
# Read in the curves from a data file
#
def defaultReadInCurves(infile, 
                        globalAbsTol=-1.0, 
                        globalRelTol=-1.0, 
                        skip_perf_curves=False, 
                        die_on_duplicate_curves=True):
    """
    expects a file's name, will return a dictionary of curve objects, hashed by the
    curve's name
    """

    #sys.stderr.write("DEBUG A10 globalAbsTol  = %s\n" % (globalAbsTol)) # ambyr
    #sys.stderr.write("DEBUG A10 globalRelTol  = %s\n" % (globalRelTol))
    
    defaultAbsTol=1.0e-8
    if globalAbsTol >= 0: defaultAbsTol = globalAbsTol

    defaultRelTol=1.0e-8
    if globalRelTol >= 0: defaultRelTol = globalRelTol


    curves = {} # our return value

    fname  = os.path.basename(infile)
    xvals  = []
    yvals  = []
    relTol = defaultRelTol
    absTol = defaultAbsTol
    c      = None
    pairID = 0

    patchLevel = ''

    inf = open(infile,"r")
    lines = filter(lambda x:x.strip(),inf)
    lines = map(remove_space,lines)
    lines = verify_number_pairs(lines)

    ## this nasty expression converts our list of strings
    ##into a list of strings (for curve names) and 2-item lists
    ##of numbers (for data) (n = number of columnns)
    datify = lambda x:x if ('#' in x) or ('end' in x) else map(eval,x.split()[:2])
    data = map(datify,lines)

    for d in data:
        #print d
        #
        # We are done reading in the x-y data under 3 conditions:
        #
        # 1) We cncounter an 'end' statement
        # 2) We encounter a '#' comment line
        # 3) We reach the end of the file 
        #
        # c may be none if this was a performance curve we are ignoring, in that case
        # do not add the x and y vals to it
        #
        # len xvals will be set to 0 after the curve is added when the 1st '#' is
        # encountered.  Thus check the length of xvals so we do not attempt to add
        # the curve more than once on subsequent '#' comments.
        #
        # c may be none under certain conditions, such as when we ignore a curve
        # perhaps because it is a performance based curve we choose to ignore.
        #
        if ("end" == d[0:3]) or (('#' in d) and (len(xvals) > 0)):
            if c:
                #
                # This section changes single point x-y vals to two points to 
                # create a line that gnuplot can handle.   The second line
                # has the same yval but modifies the xval (either doubling it,
                # or, if it is 0 adding 1 to it)
                #
                if len(xvals) == 1:
                    xvals.append(dup_xval(xvals[0]))
                    yvals.append(yvals[0])

                c.xvals = np.array(xvals)
                c.yvals = np.array(yvals)
                key = (c.name)
                if key not in curves:
                    curves[key] = c
                else:
                    sys.stderr.write("%s contains two copies of %s! Fix this!\n" % (infile, c.name))
                    if die_on_duplicate_curves:
                        sys.exit(2)
                c      = None
            xvals = []
            yvals = []
            relTol = defaultRelTol
            absTol = defaultAbsTol

        if '#' in d:
            if "# rel " == d[0:6]: 
                if globalRelTol < 0:
                    if is_a_number(d[6:]):
                        relTol = float(d[6:])
                    else:
                        sys.stderr.write("%s does not contain a valid number -- Ignoring tolerance\n" % (d))
                    continue
            elif "# abs " == d[0:6]: 
                if globalAbsTol < 0:
                    if is_a_number(d[6:]):
                        absTol = float(d[6:])
                    else:
                        sys.stderr.write("%s does not contain a valid number -- Ignoring tolerance\n" % (d))
                    continue
            elif "# fileName: "== d[0:12]:
                fname = d[12:].strip()
                continue
            elif "Version______" in d:                  # Mehul Patel code version info
                index = d.index('Version______') + 1
                version = d[index:].strip() 
                patchLevel = version
            #elif "Version" in d:
            #    index = d.index(':') + 1
            #    version = d[index:].strip() 
            #    patchLevel = version.split('.')[2]
            #    continue
            elif "Version" in d and ":" in d and patchLevel == '':
                index = d.index(':') + 1
                version = d[index:].strip()
                patchLevel = version.split('.')[2]
                if "-" in patchLevel:
                    patchLevel = patchLevel.split('-')[0]
                continue
            elif "# Build Date"== d[0:12]:
                continue
            #elif " Version:"== d[10:18]:
            #    continue
            #elif " Version:"== d[9:17]:
            #    continue
            #elif " Version:"== d[5:13]:
            #    continue
            #elif " Hash:"== d[10:15]:
            #    continue
            #elif " Hash:"== d[9:14]:
            #    continue
            #elif " Hash:"== d[5:1]:
            #    continue
            elif "Hash:" in d:
                continue
            elif "Version:" in d:
                continue
            elif "# Build Date"== d[0:12]:
                continue
            elif "# Build Host"== d[0:12]:
                continue
            elif "# Build OS"== d[0:10]:
                continue
            elif "# Target OS"== d[0:11]:
                continue
            elif "# Compile"== d[0:9]:
                continue
            else:
                ## look for '#' to indicate start of new curve
                # line has name of 
                xvals = []
                yvals = []
                pairID += 1
                myname = adjust_curve_name(d[1:])
                if skip_perf_curves:
                    if  myname.find('walltime') >= 0 \
                     or myname.find('maxProcessorMemory') >= 0 \
                     or myname.find('maxNodeMemory') >= 0 \
                     or myname.find('minProcessorMemory') >= 0 \
                     or myname.find('minNodeMemory') >= 0 \
                     or myname.find('avgProcessorMemory') >= 0 \
                     or myname.find('avgNodeMemory') >= 0 \
                     or myname.find('sumProcessorMemory') >= 0 \
                     or myname.find('deltaAverageWalltime') >= 0 : 

                        pairID -= 1
                    else:
                        c = UltraCurve(myname, fname, absTol, relTol, pairID, patchLevel);
                else:
                    c = UltraCurve(myname, fname, absTol, relTol, pairID, patchLevel);
                continue

        #
        # end already processed above, just ignore it for now
        #
        elif "end" == d[0:3]: 
            continue

        #
        # This must be a set if x-y data.  Add the data to the x and yvals
        # 
        else:
            if len(d) == 2:
                xvals.append(d[0])
                yvals.append(d[1])
            else:
                sys.stderr.write("Do not know what to do with '%s' \n" % d)
                sys.exit(2)

    #
    # At end of file, if the xvals and yvals from the
    # prior curve have not been added, then do the same as is done
    # when an explicit 'end' is encountered.  This allows for codes
    # to not have to put the 'end' at the end of their curves.
    #
    # c may be none if this was a performance curve we are ignoring, in that case
    # do not add the x and y vals to it
    if len(xvals) > 0:
        if c:
            if len(xvals) == 1:
                xvals.append(dup_xval(xvals[0]))
                yvals.append(yvals[0])
            c.xvals = np.array(xvals)
            c.yvals = np.array(yvals)
            key = (c.name)
            if key not in curves:
                curves[key] = c
            else:
                sys.stderr.write("%s contains two copies of %s! Fix this!\n" % (infile, c.name))
                if die_on_duplicate_curves:
                    sys.exit(2)
            c      = None

    #sys.stderr.write("DEBUG A99 relTol  = %s\n" % (relTol)) # ambyr
    #sys.stderr.write("DEBUG A99 absTol  = %s\n" % (absTol)) # ambyr


    return curves

################################################################################    
        
class curve:
    """ this is the main data structure for representing time - value curves. It provides basic
    fields for time, yvals, tolerances, and a curve name. (xvals, yvals, absTol, relTol, and name)

    In addition, it provides three helper functions for writing absolute and relative difference
    data, as well as outputting gnuplot data. These provide some bookkeeping so the curves are aware
    of where in the file they are writing to (useful for later gnuplot scripting)
    
    """
    def __init__(self,name, fname,absTol,relTol, pairID = 0):
        self.name   = name
        self.fname  = fname
        self.absTol = absTol
        self.relTol = relTol
        self.pairID = pairID
        self.xvals  = None
        self.yvals  = None

        self.normalizeName()
        
    def __repr__(self):
        return "%s: x=%s, y= %s" % \
               (self.name,repr(self.xvals),repr(self.yvals))

    def normalizeName( self ):
        self.name = self.name.replace('(', '').replace(')', '')
        self.name = self.name.replace(':, ', '___')

    def writeCompareDataToFile(self, f,curve2, numPairs):
        
        f.write("#Pair %i of %i: curve %s and baseline %s\n"
                      %(self.pairID, numPairs, self.name, curve2.name ))
        f.write("#Curve Label                 : %s\n" % self.name)
        f.write("#Curve Abs Tolerance         : %g\n" % self.absTol)
        f.write("#Curve Rel Tolerance         : %g\n" % self.relTol)
        f.write("#Baseline Label              : %s\n" % curve2.name)
        f.write("#Average difference          : %g\n" %self.aveAbsDiff)
        f.write("#Average relative difference : %g\n" %self.aveRelDiff)
        f.write("#Maximum absolute difference : %g\n" %self.maxAbsDiff)        
        f.write("#Maximum relative difference : %g\n" %self.maxRelDiff)

        ##this is for tapestry - may not be needed long term
        if self.maxAbsDiff > self.absTol:
            f.write("#TAP_MAX_ABS^FAIL^%g^1^%s^%g^2^%s^%g\n" %
                          (self.maxAbsDiff,self.name,self.absTol,curve2.name,self.absTol))
        else:
            f.write("#TAP_MAX_ABS^PASS^%g^1^%s^%g^2^%s^%g\n" %
                          (self.maxAbsDiff,self.name,self.absTol,curve2.name,self.absTol))
            
        if self.maxRelDiff > self.relTol:
            f.write("#TAP_MAX_REL^FAIL^%g^1^%s^%g^2^%s^%g\n\n\n" %
                          (self.maxRelDiff,self.name,self.relTol,curve2.name,self.relTol))
        else:
            f.write("#TAP_MAX_REL^PASS^%g^1^%s^%g^2^%s^%g\n\n\n" %
                          (self.maxRelDiff,self.name,self.relTol,curve2.name,self.relTol))            

    def writeGnuPlotDataToFile(self,f,index):
        """ f is a file object. opening and closing of the file is assumed to be
        the responsibility of the caller"""
        for x, y in zip_longest(self.xvals, self.yvals):
            f.write("%24.12e\t%24.12e\n" % (x,y))
        f.write("\n\n")
        self.gnuPlotName = f.name
        self.gnuIndex = index

    def writeAbsDiffDataToFile(self,f,index):
        """ f is a file object. opening and closing of the file is assumed to be
        the responsibility of the caller"""
        f.write("#Absolute difference curve for %s\n" % self.name)
        for x, y in zip_longest(self.allXvals, self.absDiff):
            f.write("%24.12e\t%24.12e\n" %(x,y))
        f.write("\n\n")
        self.absDiffName = f.name
        self.absDiffIndex = index
        
    def writeRelDiffDataToFile(self,f,index):
        """ f is a file object. opening and closing of the file is assumed to be
        the responsibility of the caller"""
        f.write("#Relative difference curve for %s\n" % self.name)
        for x, y in zip_longest(self.allXvals, self.relDiff):
            f.write("%24.12e\t%24.12e\n" %(x,y))
        f.write("\n\n")
        self.relDiffName = f.name
        self.relDiffIndex = index

    def compareWith(self, curve2, use_and=False):
        
        checkFailed = False

        # ambyr
        #print "DEBUG 220 " 
        #print self.relTol
        #print self.absTol
        #print "DEBUG 230 "

        ## gather list of unique x's
        self.allXvals = np.sort(np.union1d(self.xvals,curve2.xvals))

        #print "SAD DEBUG before np call"

        ## where yvals aren't defined, interpolate curves to those yvals
        interp1 = np.interp(self.allXvals,self.xvals,self.yvals)

        #print "SAD DEBUG after np call"
        interp2 = np.interp(self.allXvals,curve2.xvals,curve2.yvals)

        ## using the two interpolated curves, calculate an absolute difference curve
        self.absDiff = abs(interp1 - interp2)
        
        ## using the two interpolated curves, calculate a relative difference curve
        
        scale = abs(interp1) + abs(interp2)
        
        ## We eliminate any places where we could divide by 0 in scale by setting them to 1.
        ## Note that this must be accurate because |A|+|B| = 0 iff |A| = 0 and |B| = 0,
        ## which implies |A-B| = 0. Hence, we are changing divisions of 0/0 to 0/1. The
        ## absolute difference is 0, so the relative diff will also be set to 0.
        ones = np.ones_like(interp2)
        scale = np.where(scale != 0,scale,ones)
        self.relDiff = self.absDiff/scale

        ## Compute average difference = 1/(int_len) Integral |A-B|
        try:
            interval = self.allXvals[-1] - self.allXvals[0]
            interval = 1 if interval == 0 else interval
            
            self.aveAbsDiff = 1/interval*np.trapz(self.absDiff,self.allXvals)

            ## Compute average relative difference = 1/(int_len) Integral |A-B|/(|A|+|B|)
            self.aveRelDiff = 1/interval*np.trapz(self.relDiff,self.allXvals)

            ## Compute maximum absolute difference = max{|A-B|}
            self.maxAbsDiff = self.absDiff.max();

            ## Compute maximum relative difference = max{|A-B|/(|A|+|B|)}
            self.maxRelDiff = self.relDiff.max();

            if use_and:
                if self.maxRelDiff > self.relTol and (self.maxAbsDiff > self.absTol):
                    self.failed = True
                    checkFailed = True
                else:
                    self.failed = False

            else:
                if self.maxRelDiff > self.relTol or (self.maxAbsDiff > self.absTol):
                    self.failed = True
                    checkFailed = True
                else:
                    self.failed = False

        except IndexError, error:
            print 'IndexError: %s' % error
            print 'Length of self.allXvals: %s' % len(self.allXvals)

        return checkFailed

    def createOutputPlots( self, gp, curve2, numPairs, dir, kernel ):
        """
        uses the data stored in curves and baselines to construct and execute
        gnuplot commands, generating .png files depicting original data,
        absolute and relative differences for each curve/baseline pair that
        failed the comparison.
        """
        type = 'small'
        xaxis = "time (micro sec)"
        yaxis = "value"

        #sys.stderr.write("DEBUG 020 xaxis = %s\n" % (xaxis))

        dataPlot = os.path.join(dir,"%s-%03d-datacurves-%s-%s.png" % (kernel,self.pairID,type,self.name))
        dataTitle = "Pair %i of %i: Actual Data Curves" %(self.pairID,numPairs)

        ## relative difference curve
        relPlot = os.path.join(dir,"%s-%03d-rel_diffcurves-%s-%s.png"% (kernel,self.pairID,type,self.name))
        relTitle= "Pair %i of %i: Relative Difference Curve" %(self.pairID,numPairs)

        ## absolute difference curve
        absPlot = os.path.join(dir,"%s-%03d-abs_diffcurves-%s-%s.png"% (kernel,self.pairID,type,self.name))
        absTitle= "Pair %i of %i: Absolute Difference Curve" %(self.pairID,numPairs)

        ## Build the 'plot' command for curve and baseline to be given to GnuPlot, respectively
        ## points GnuPlot to the pdl.reform.curves file created earlier
        dataCommand = "plot \"%s\" index %i using 1:2 title \"%s\" with linespoints, " % (self.gnuPlotName,self.gnuIndex,self.name)
        dataCommand +="\"%s\" index %i using 1:2 title \"%s\" with linespoints\n" % (curve2.gnuPlotName,curve2.gnuIndex,curve2.name)

        ## Build the 'plot' command for the relative difference curves given to GnuPlot respectively
        ## points GnuPlot to the pdl.rel-diff.curves file created earlier

        relCommand = "plot \"%s\" index %i using 1:2 title 'Relative Difference' with linespoints\n" %(self.relDiffName,self.relDiffIndex)


        ## Build the 'plot' command for the absoute difference curves given to GnuPlot respectively
        ## points GnuPlot to the pdl.abs-diff.curves file created earlier
        absCommand = "plot \"%s\" index %i using 1:2 title 'Absolute Difference' with linespoints\n" % (self.absDiffName,self.absDiffIndex)

        gp.write( "set term png small\n")
        gp.write( "set size 0.8, 0.8\n")

        gp.write( "set output \"%s\"\n" % dataPlot)
        gp.write( "set title \"%s\"\n" % dataTitle)
        gp.write( "set xlabel \"%s\"\n" % xaxis)
        gp.write( "set ylabel \"%s\"\n" % yaxis)
        gp.write( "set grid\n")
        gp.write( "set key left box\n")
        gp.write( dataCommand)

        gp.write( "set output \"%s\"\n" % relPlot)
        gp.write( "set title \"%s\"\n" % relTitle)
        gp.write( relCommand)

        gp.write( "set output \"%s\"\n" % absPlot)
        gp.write( "set title \"%s\"\n" % absTitle)
        gp.write( absCommand)


####################################################

class UltraCurve( curve ):
    
    def __init__(self, name, fname, absTol, relTol, pairID, version):
        curve.__init__( self, name, fname, absTol, relTol, pairID)
        self.version = version
        self.curve_name = '%s_%s'   % (self.version, self.name)
        self.label      = '%s # %s' % (self.version, self.name)
        
    def writeCompareDataToFile(self, f,curve2, numPairs):

        c2ID = numPairs + curve2.pairID
        
        f.write("#Pair %i of %i: Curve %s and Curve %s\n"
                      %(self.pairID, numPairs, self.pairID, c2ID))
        f.write("#Curve 1 Label              : %s\n" % self.label)
        f.write("#Curve 1 Abs Tolerance      : %g\n" % self.absTol)
        f.write("#Curve 1 Rel Tolerance      : %g\n" % self.relTol)
        f.write("#Curve 2 Label              : %s\n" % curve2.label)
        f.write("#Curve 2 Abs Tolerance      : %g\n" % curve2.absTol)
        f.write("#Curve 2 Rel Tolerance      : %g\n" % curve2.relTol)
        f.write("#Average difference         : %g\n" %self.aveAbsDiff)
        f.write("#Average relative difference: %g\n" %self.aveRelDiff)
        f.write("#Maximum absolute difference: %g\n" %self.maxAbsDiff)        
        f.write("#Maximum relative difference: %g\n" %self.maxRelDiff)

        ##this is for tapestry - may not be needed long term
        if self.maxAbsDiff > self.absTol:
            f.write("#TAP_MAX_ABS^FAIL^%g^%d^%s^%g^%d^%s^%g\n" %
                          (self.maxAbsDiff,self.pairID, self.label,self.absTol,
                           c2ID, curve2.label,self.absTol))
        else:
            f.write("#TAP_MAX_ABS^PASS^%g^%d^%s^%g^%d^%s^%g\n" %
                          (self.maxAbsDiff,self.pairID, self.label,self.absTol,
                           c2ID, curve2.label,self.absTol))
            
        if self.maxRelDiff > self.relTol:
            f.write("#TAP_MAX_REL^FAIL^%g^%d^%s^%g^%d^%s^%g\n\n" %
                          (self.maxRelDiff,self.pairID, self.label,self.relTol,
                           c2ID, curve2.label,self.relTol))
        else:
            f.write("#TAP_MAX_REL^PASS^%g^%d^%s^%g^%d^%s^%g\n\n" %
                          (self.maxRelDiff,self.pairID, self.label,self.relTol,
                           c2ID, curve2.label,self.relTol))            

    
    # SAD is calling this one it seems, not the other one
    def createOutputPlots( self, gp, curve2, numPairs, type, dir, kernel):
        """
        uses the data stored in curves and baselines to construct and execute
        gnuplot commands, generating .png files depicting original data,
        absolute and relative differences for each curve/baseline pair that
        failed the comparison.
        """
        name1 = kernel + ('-%03d-' % self.pairID)

        if cmp(self.name, curve2.name) == 0:
            name2 = 'curves-' + type + '-%s_VS_%s_%s.png' % ( self.version, curve2.version, curve2.name)
        else:
            print "createOutputPlots curve '%s' does not match curve '%s'" % (self.name, curve2.name)
            sys.exit(-1)

        data_file_name = name1 + 'data' + name2
        dataPlot = os.path.join(dir, data_file_name)
        if cmp(type,'large') == 0:
            dataTitle = "Actual Data : %s" %(self.name)
        else:
            dataTitle = "Pair %i of %i: Actual Data Curves" %(self.pairID,numPairs)

        ## relative difference curve
        rel_file_name = name1 + 'rel_diff' + name2
        relPlot = os.path.join(dir,rel_file_name)
        if cmp(type,'large') == 0:
            relTitle = "Relative Difference : %s" %(self.name)
        else:
            relTitle= "Pair %i of %i: Relative Difference Curve" %(self.pairID,numPairs)

        ## absolute difference curve
        abs_file_name = name1 + 'abs_diff' + name2 
        absPlot = os.path.join(dir, abs_file_name)
        if cmp(type,'large') == 0:
            absTitle = "Absolute Difference : %s" %(self.name)
        else:
            absTitle= "Pair %i of %i: Absolute Difference Curve" %(self.pairID,numPairs)

        ## Build the 'plot' command for curve and baseline to be given to GnuPlot, respectively
        ## points GnuPlot to the pdl.reform.curves file created earlier
        plot_cmd1 = 'plot \"%s\" index %i using 1:2 title \"%s\" with linespoints'
        plot_cmd2 = '\"%s\" index %i using 1:2 title \"%s\" with linespoints\n'
        dataCommand  = (plot_cmd1 + ", ") % (self.gnuPlotName,  self.gnuIndex,  self.label)
        dataCommand +=  plot_cmd2         % (curve2.gnuPlotName,curve2.gnuIndex,curve2.label)

        ## Build the 'plot' command for the relative difference curves given to GnuPlot respectively
        ## points GnuPlot to the pdl.rel-diff.curves file created earlier
        relCommand = ("plot " + plot_cmd2) % ( self.relDiffName,self.relDiffIndex, 'Relative Difference')

        ## Build the 'plot' command for the absolute difference curves given to GnuPlot respectively
        ## points GnuPlot to the pdl.abs-diff.curves file created earlier
        absCommand = ("plot " + plot_cmd2) % ( self.absDiffName,self.absDiffIndex, 'Absolute Difference')

        gp.write( "set output \"%s\"\n" % dataPlot)
        gp.write( "set title \"%s\"\n" % dataTitle)
        gp.write( dataCommand)

        gp.write( "set output \"%s\"\n" % relPlot)
        gp.write( "set title \"%s\"\n" % relTitle)
        gp.write( relCommand)

        gp.write( "set output \"%s\"\n" % absPlot)
        gp.write( "set title \"%s\"\n" % absTitle)
        gp.write( absCommand)


    def writeJavaScriptCurves(self, f, curve2 ):

        def writeCurve(f, type, id, vals):
            f.write('curve%d_%s = new Array(' % (id, type))
            for x in vals[:-1]:
                f.write('%g,' % x)
            f.write('%g);\n' % vals[-1])
            
        f.write('\n\n// %s\n' % self.label)
        
        writeCurve(f, 'new_x', self.pairID, self.xvals)
        writeCurve(f, 'new_y', self.pairID, self.yvals)

        f.write('\n// %s\n' % curve2.label)
        
        writeCurve(f, 'baseline_x', curve2.pairID, curve2.xvals)
        writeCurve(f, 'baseline_y', curve2.pairID, curve2.yvals)


####################################################################################

class UltraComparator:

    def __init__(self, base_file_name, new_file_name, reader=defaultReadInCurves,
                 verbose=True, use_and=False, absTol=-1.0, relTol=-1.0, 
                 skip_perf_curves=False,
                 die_on_duplicate_curves=True,
                 xaxis='time (micro sec)',
                 yaxis='value'):
        
        self.base_file_name = base_file_name
        self.new_file_name  = new_file_name
        self.verbose        = verbose
        self.use_and        = use_and
        self.absTol         = absTol
        self.relTol         = relTol
        self.skip_perf_curves = skip_perf_curves
        self.die_on_duplicate_curves = die_on_duplicate_curves
        self.xaxis = xaxis
        self.yaxis = yaxis

        #sys.stderr.write("DEBUG 010 self.xaxis  = %s\n" % (self.xaxis))
        #sys.stderr.write("DEBUG 010 self.absTol = %s\n" % (self.absTol))
        #sys.stderr.write("DEBUG 010 self.relTol = %s\n" % (self.relTol))
        
        self.curves = reader(self.new_file_name, self.absTol, self.relTol, self.skip_perf_curves, self.die_on_duplicate_curves)
        if verbose:
            print "%i curves read in" % len(self.curves)
            
        self.baselines = reader(self.base_file_name, self.absTol, self.relTol, self.skip_perf_curves, self.die_on_duplicate_curves)
        if verbose:
            print "%i baselines read in" % len(self.baselines)



    def comparecurves(self):
        """curves, baselines are each expected to be a list of curve objects.
        relativeTols should be the maximum allowable tolerance.

        Return Value: True if all curves have maxRelativeDifference less than their
        respective tolerances

        comparecurves appends/modifies fields to the curves (not baselines) that
        stores information about the curves' differences from the baselines.
        fields written to are: 
        absDiff / relDiff: absolute / relative difference (interpolated curves)
        aveAbsDiff / aveRelDiff:   average absolute / relative difference
        maxAbsDiff/ maxaveRelDiff:  max relative/absolute  difference. """


        comparisonFailed = False

        for c1Key in self.curves.keys(): 
            c1 = self.curves[c1Key]


            if self.verbose:
                sys.stdout.write('Checking curve ' + c1.name )

        
            if c1Key in self.baselines.keys(): 
                c2 = self.baselines[c1Key]
            else:
                sys.stdout.write(' - FAILED\n')
                sys.stdout.write("  Curve %s is not in baseline file %s!\n" % (c1Key,
                                                                               self.base_file_name))
                comparisonFailed = True
                # set c1.failed to False so that this curve is not processed later
                c1.failed = False 
                continue


            resultFailed = c1.compareWith(c2, self.use_and)


            if self.verbose:
                if resultFailed:
                    sys.stdout.write(' - FAILED\n')
                else:
                    sys.stdout.write(' - passed\n')
                    
                
            comparisonFailed =  comparisonFailed or resultFailed


        return comparisonFailed


    def outputDiffInfo(self, dirname, kernel):
        """ Generates pdl.comparison.results, pdl.reform.curves, pdl.abs-diff.curves,
        and pdl.rel-diff.curves. curvefile and baseline file should be the file names. 
        """
        compare = open(os.path.join(dirname, kernel+".pdl.comparison.results"),'w')
        reform =  open(os.path.join(dirname, kernel+".pdl.reform.curves"),'w')
        absDiff = open(os.path.join(dirname, kernel+".pdl.abs-diff.curves"),'w')
        relDiff = open(os.path.join(dirname, kernel+".pdl.rel-diff.curves"),'w')

        cLen = len(self.curves)
        bLen = len(self.baselines)
        numPairs = max(cLen,bLen)

        tmp_curves = self.curves.values()
        tmp_curves.sort(cmp=lambda x,y: cmp(x.pairID, y.pairID))

        compare.write("\n#Results of comparison of curves in %s and %s\n" % (self.new_file_name,
                                                                             self.base_file_name))

        reform.write("#Reformatted data for GnuPlot from %s and %s\n" %(self.new_file_name,
                                                                        self.base_file_name))

        relDiff.write("#Difference curves generated from %s and %s\n" % (self.new_file_name,
                                                                         self.base_file_name))

        absDiff.write("#Difference curves generated from %s and %s\n" % (self.new_file_name,
                                                                         self.base_file_name))    
        for c in tmp_curves:
            try:
                b = self.baselines[c.name]

                ##Comparison.results
                c.writeCompareDataToFile(compare, b, numPairs)

                ##reform.curves will contain a GnuPlot friendly file with all original curve data.
                ## the curve objects here will have an 0 based index,gnuIndex, for easy reference later on
                c.writeGnuPlotDataToFile(reform, (2*c.pairID - 2))
                b.writeGnuPlotDataToFile(reform, (2*c.pairID - 1))

                ##diff.curves
                c.writeRelDiffDataToFile(relDiff,c.pairID-1)    
                c.writeAbsDiffDataToFile(absDiff,c.pairID-1)

            except KeyError, error:
                #sys.stdout.write("Curve %s is not in baseline file %s.\n" % (c.name,
                #                                                             self.base_file_name))
                pass
                

        compare.close()
        reform.close()
        absDiff.close()
        relDiff.close()


    def outputJavaScriptCurves(self, dirname, kernel):
        """
        Generates .pdl.curves.js file.
        """
        jsFile = open(os.path.join(dirname, kernel + ".pdl.curves.js"),'w')

        #tmp_curves = self.curves.values()
        tmp_curves = [ c for c in self.curves.values() if c.failed ]
        tmp_curves.sort(cmp=lambda x,y: cmp(x.pairID, y.pairID))

        jsFile.write("//Reformatted data for JavaScript from %s and %s\n" %(self.new_file_name,
                                                                            self.base_file_name))
        jsFile.write('\n//Arrays with baseline and new curves\n')
        
        for c in tmp_curves:
            
            b = self.baselines[c.name]

            c.writeJavaScriptCurves(jsFile,b)
            
        jsFile.close()


    def outputPlots(self, gnuplot, dir, kernel, type):
        """
        uses the data stored in curves and baselines to construct and execute
        gnuplot commands, generating .png files depicting original data,
        absolute and relative differences for each curve/baseline pair that
        failed the comparison.
        """
        pixels = {'small':'512,384', 'medium':'800,600', 'large':'1280,960'}

        numPairs = max(len(self.curves),len(self.baselines))

        #sys.stderr.write("DEBUG 030 self.xaxis = %s\n" % (self.xaxis))

        ## open gnuplot just the once
        gp_proc = Popen( gnuplot+" -persist", shell=True, stdin=PIPE)
        gp = gp_proc.stdin

        failed_curves = [ c for c in self.curves.values() if c.failed ]

        gp.write( "set xlabel \"%s\" textcolor rgb \"blue\"\n" % self.xaxis)
        gp.write( "set ylabel \"%s\" textcolor rgb \"blue\"\n" % self.yaxis)
        gp.write( "set grid\n")
        gp.write( 'set format x "%3.1e"\n')
        gp.write( 'set format y "%g"\n')
        gp.write( 'set xtics in offset 0, -2.5 rotate by 90\n')
        gp.write ('set xtics font "Times-Roman, 10" \n')
        gp.write( 'set key left Left reverse box font "Sans,8"\n')
        gp.write( "set term png size %s\n" % pixels[type] )

        for c in failed_curves:
            # If we can parse a _vs_ out of the curve name, then do so and use
            # that to set the xaxis 
            #
            # If creating a 'large' image, then also replace the yaxis, 
            # but there is not enough room in the 'small' images, so leave
            # those be.
            vs_start = c.name.find('_vs_')
            if vs_start > 0:
                vs_xaxis = c.name[vs_start + 4:]
                vs_yaxis = c.name[0:vs_start]
                gp.write( "set xlabel \"%s\" textcolor rgb \"blue\"\n" % vs_xaxis)
                if cmp(type,'large') == 0:
                    gp.write( "set ylabel \"%s\" textcolor rgb \"blue\"\n" % vs_yaxis)
                else:
                    gp.write( "set ylabel \"%s\" textcolor rgb \"blue\"\n" % vs_yaxis[:35])
            #else:
            #    gp.write( "set ylabel \"%s\"\n" % self.xaxis)
            #    gp.write( "set xlabel \"%s\"\n" % self.yaxis)
                
           
            c.createOutputPlots(gp, self.baselines[c.name], numPairs, type, dir, kernel)

            #
            # Reset the xlabel and ylabel to defaults
            #
            gp.write( "set xlabel \"%s\" textcolor rgb \"blue\"\n" % self.xaxis)
            gp.write( "set ylabel \"%s\" textcolor rgb \"blue\"\n" % self.yaxis)

        gp.close()
        if gp_proc.wait() != 0:
            print "Errors creating plot files!"

###########################################################################################3

class UltraCheckBase2:
  def __init__(self):
    self.startingDirectory = os.getcwd()
  
  def addOptions( self, parser ):
    parser.add_option('-k', '--kernel', action='store', dest='kernel',
                      default="",
                      help='base name for output files')

    
    parser.add_option('-b', '--curvefile_baseline', action='store', dest='curvefile_baseline',
                      default="",
                      help='baseline results curve file')


    parser.add_option('-c', '--curvefile', action='store', dest='curvefile',
                      default="",
                      help='new results curve file.')


    parser.add_option('-d', '--directory', action='store', dest='directory',
                      default="",
                      help='directory to run in, has input files it it.')


    parser.add_option('-a', '--abs', action='store', type='float', dest='abs_override',
                      default=-1.0,
                      help='absolute difference criteria, overrides per curve value')


    parser.add_option('-r', '--rel', action='store', type='float', dest='rel_override',
                      default=-1.0,
                      help='relative difference criteria, overrides per curve value')

    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      default=False,
                      help='Generate verbose output')


    parser.add_option('--use_and', action='store_true', dest='use_and',
                      default=False,
                      help='And comparison results instead of "or"-ing them.')


    parser.add_option('-n', '--no-cleanup', action='store_false', dest='cleanup',
                      default=True,
                      help='Do not clean up intermediate files created by comparison')

    parser.add_option("-g", "--gnuplot", type = "string", dest = "gnuplot",
                      default='',
                      help='Path to gnuplot executable to use for making images')

    parser.add_option("--skip-perf", type = "string", dest = "skip_perf_curves",
                      default=False,
                      help='Skip performance based curves such as time and memory')

    parser.add_option("--die-on-dups", type = "string", dest = "die_on_duplicate_curves",
                      default=True,
                      help='Die if duplicate curves are detected')

    parser.add_option("--xaxis", action='store', dest='default_xaxis',
                      default="time (micro sec)",
                      help='Default xaxis label.')

    parser.add_option("--yaxis", action='store', dest='default_yaxis',
                      default="value",
                      help='Default yaxis label.')

  def cleanupFiles( self, folder, kernel, all=False ):
     """
     Cleanup files created by comparison.
     """
     files_re_str  = "\.pdl\..curves.*|\.curves.without.matches"
     if all:
       files_re_str += "|-[0-9].+\.png|\.pdl\.comparison\.results"

     files_re = re.compile( '^%s(%s)$' % (kernel, files_re_str) )

     for a_file in listfiles(folder):
       if files_re.match(a_file):
         the_file = os.path.join(folder, a_file)
         try:
           os.remove(the_file)
         except IOError, error:
             sys.stderr.write('WARNING: IOError removing file: %s' % a_file)
             sys.stderr.write('  Error: %s\n' % error.args)


  def processCommandLineArgs(self):
    # ---------------------------------------------------------------------------------------------
    # Process command line args
    # ---------------------------------------------------------------------------------------------
    parser = OptionParser()
    self.addOptions(parser)

    #print sys.argv # ambyr

    (self.options, self.inputFiles) = parser.parse_args(sys.argv[1:])

    #print self.options.abs_override # ambyr
    #print self.options.rel_override # ambyr

    if   (self.options.kernel == ""): 
        print "UltraCheck --kernel=xxx not specified"
        sys.exit(-1)
    elif (self.options.curvefile_baseline == ""): 
        print "UltraCheck --curvefile_baseline=xxx not specified"
        sys.exit(-1)
    elif (self.options.curvefile == ""): 
        print "UltraCheck --curvefile=xxx not specified"
        sys.exit(-1)


    if self.options.directory:
      # Go to directory with files to be compared
      os.chdir(self.options.directory)
      
    # ---------------------------------------------------------------------------------------------
    # Verify both curve files exist
    # Put in some sleeps and a while loop to account for rzuseq file slowness
    # ---------------------------------------------------------------------------------------------
    total_sleep_time = 0
    while not os.path.isfile(self.options.curvefile_baseline):
        print "curvefile_baseline %s does not exist in %s, slept %d secs" % (self.options.curvefile_baseline, os.getcwd(), total_sleep_time)
        time.sleep(30)
        total_sleep_time = total_sleep_time + 30
        if total_sleep_time > 120:
            print "Bypassing check, curvefile_baseline %s does not exist in %s" % (self.options.curvefile_baseline, os.getcwd())
            sys.exit(-1)

    total_sleep_time = 0
    while not os.path.isfile(self.options.curvefile):
        print "curvefile %s does not exist in %s, slept %d secs" % (self.options.curvefile, os.getcwd(), total_sleep_time)
        time.sleep(30)
        total_sleep_time = total_sleep_time + 30
        if total_sleep_time > 120:
            print "Bypassing check, curvefile %s does not exist in %s" % (self.options.curvefile, os.getcwd())
            sys.exit(-1)

  def runCheck(self, here):
    # ---------------------------------------------------------------------------------------------
    # Let's do the comparison
    # ---------------------------------------------------------------------------------------------


    return_code = 0
    comparator  = UltraComparator(self.options.curvefile_baseline,
                                  self.options.curvefile,
                                  verbose=self.options.verbose,
                                  use_and=self.options.use_and,
                                  absTol=self.options.abs_override,
                                  relTol=self.options.rel_override,
                                  skip_perf_curves=self.options.skip_perf_curves,
                                  die_on_duplicate_curves=self.options.die_on_duplicate_curves,
                                  xaxis=self.options.default_xaxis,
                                  yaxis=self.options.default_yaxis)


    #sys.stderr.write("DEBUG 040 comparator.xaxis = %s\n" % (comparator.xaxis))
    #sys.stderr.write("DEBUG 050 self.options.default_xaxis = %s\n" % (self.options.default_xaxis))

    
    if comparator.comparecurves():
        ## if significant differences exist, output info and then exit with code 1
        outdir = '.'

        comparator.outputDiffInfo(outdir, self.options.kernel)
        comparator.outputJavaScriptCurves( outdir, self.options.kernel)
        
        if self.options.gnuplot:
            comparator.outputPlots(self.options.gnuplot, outdir, self.options.kernel, 'small')
            comparator.outputPlots(self.options.gnuplot, outdir, self.options.kernel, 'large')

        return_code = 1


    return ( return_code )
  

  def main(self):
    self.processCommandLineArgs()


    # ---------------------------------------------------------------------------------------------
    #
    # OK, we have both sets of curve files.
    #
    # Before we do the comparison, cleanup all existing comparison files which may exist
    #
    # Let's do the comparison
    #
    # After comparison, cleaup unneeded comparsion files (but leave essential files, such
    #   as .png and the comparision.results file)
    #
    # ---------------------------------------------------------------------------------------------
    here = os.getcwd()          # current directory

    #
    # WARNING: These cleanup functions are not safe when running multiple tests in a directory
    #          where the kernel name of one test is a substring of another kernel name!!

    # Check if the above is still true!
    if self.options.cleanup:
      self.cleanupFiles( here, self.options.kernel, all=True )


    return_code = self.runCheck( here )

    if self.options.cleanup:
      self.cleanupFiles( here, self.options.kernel)

    if self.options.directory:
      os.chdir(self.startingDirectory)
      
    return ( return_code )


###########################################################################################3


if __name__ == "__main__":
    """ Takes 2 arguments, a ultra format curvefile, and a second file
    to compare to. Exits with 0 if curves pass within tolerances, 1 if not. 
    """
    dbg = True
    parser = optparse.OptionParser()

    ## argument to check results of pdldiff script
    ## pdldiff option included but ignored at the moment
    parser.add_option("-p", "--pdldiff", type = "string", dest = "pdldiff" )
    parser.add_option("-g", "--gnuplot", type = "string", dest = "gnuplot",
                      default='')
    (options, args) = parser.parse_args()

    assert len(args) == 2
    curvefile = args[0]
    baselinefile = args[1]
    assert os.path.exists(curvefile) 
    assert os.path.exists(baselinefile)
    #    assert options.gnuplot
    if options.gnuplot:
        assert os.path.exists(options.gnuplot)

    comparator = UltraComparator(baselinefile, curvefile)
    
    if comparator.comparecurves():
        ## if significant differences exist, output info and then exit with code 1
        outdir = curvefile + ".curvecheck"
        if os.path.exists(outdir):
            shutil.rmtree(outdir)

        os.mkdir(outdir)
        kernel = curvefile.replace('.ult','')

        comparator.outputDiffInfo(outdir, kernel)
        comparator.outputJavaScriptCurves( outdir, kernel)
        
        if options.gnuplot:
            #comparator.outputPlots(options.gnuplot, outdir, kernel,'small', options.default_xaxis, options.default_yaxis)
            #comparator.outputPlots(options.gnuplot, outdir, kernel,'large', options.default_xaxis, options.default_yaxis)
            comparator.outputPlots(options.gnuplot, outdir, kernel,'small')
            comparator.outputPlots(options.gnuplot, outdir, kernel,'large')

        sys.exit(1)
    else:
        sys.exit(0)



    

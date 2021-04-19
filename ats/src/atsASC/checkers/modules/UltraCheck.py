#!/usr/bin/env python

from six.moves import zip_longest
import os
import sys
import re
import optparse
import glob
import shutil
import numpy as np
from subprocess import Popen, PIPE
from optparse import OptionParser

from atsASC.modules.ASC_utils import listfiles


####################################################################################

def defaultReadInCurves(infile, globalAbsTol=-1.0, globalRelTol=-1.0):
    """
    expects a file's name, will return a dictionary of curve objects, hashed by the
    curve's name
    """

    curves = {} # our return value

    fname  = os.path.basename(infile)
    xvals  = []
    yvals  = []
    relTol = 1.e-8
    absTol = 1.e-8
    c      = None
    pairID = 0

    patchLevel = ''

    inf = open(infile,"r")
    lines = filter(lambda x:x.strip(),inf)
    ## this nasty expression converts our list of strings
    ##into a list of strings (for curve names) and 2-item lists
    ##of numbers (for data) (n = number of columnns)
    datify = lambda x:x if ('#' in x) or ('end' in x) else map(eval,x.split()[:2])
    data = map(datify,lines)

    for d in data:
        if '#' in d:
            if "# rel " == d[0:6]: 
                relTol = eval(d[6:])
                continue
            elif "# abs " == d[0:6]: 
                absTol = eval(d[6:])
                continue
            elif "# fileName: "== d[0:12]:
                fname = d[12:].strip()
                continue
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
            elif "# Target OS"== d[0:11]:
                continue
            elif "# Build Host"== d[0:12]:
                continue
            elif "# Compile"== d[0:9]:
                continue
            else:
                ## look for '#' to indicate start of new curve
                # line has name of 
                xvals = []
                yvals = []
                pairID += 1
                if globalAbsTol > 0:
                    absTol = globalAbsTol
                if globalRelTol > 0:
                    relTol = globalRelTol
                c = UltraCurve(d[1:].strip(), fname, absTol, relTol, pairID, patchLevel);
                continue

        elif "end" == d[0:3]: 
            ## init arrays and append curve object to output array
            c.xvals = np.array(xvals)
            c.yvals = np.array(yvals)
            key = (c.name)
            if key not in curves:
                curves[key] = c

            else:
                sys.stderr.write("%s contains two copies of %s! Fix this!\n" % (infile,
                                                                                c.fname+c.name))
                sys.exit(2)

            c      = None
            absTol = 1.e-8
            relTol = 1.e-8

        else:
            xvals.append(d[0])
            yvals.append(d[1])

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
            f.write("%g\t%g\n" % (x,y))
        f.write("\n\n")
        self.gnuPlotName = f.name
        self.gnuIndex = index

    def writeAbsDiffDataToFile(self,f,index):
        """ f is a file object. opening and closing of the file is assumed to be
        the responsibility of the caller"""
        f.write("#Absolute difference curve for %s\n" % self.name)
        for x, y in zip_longest(self.allXvals, self.absDiff):
            f.write("%g\t%g\n" %(x,y))
        f.write("\n\n")
        self.absDiffName = f.name
        self.absDiffIndex = index
        
    def writeRelDiffDataToFile(self,f,index):
        """ f is a file object. opening and closing of the file is assumed to be
        the responsibility of the caller"""
        f.write("#Relative difference curve for %s\n" % self.name)
        for x, y in zip_longest(self.allXvals, self.relDiff):
            f.write("%g\t%g\n" %(x,y))
        f.write("\n\n")
        self.relDiffName = f.name
        self.relDiffIndex = index

    def compareWith(self, curve2, use_and=False):
        
        checkFailed = False
        
        ## gather list of unique x's
        self.allXvals = np.sort(np.union1d(self.xvals,curve2.xvals))

        ## where yvals aren't defined, interpolate curves to those yvals
        interp1 = np.interp(self.allXvals,self.xvals,self.yvals)
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
    
    def __init__(self,name, fname,absTol, relTol, pairID, version):
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

    
    def createOutputPlots( self, gp, curve2, numPairs, type, dir, kernel ):
        """
        uses the data stored in curves and baselines to construct and execute
        gnuplot commands, generating .png files depicting original data,
        absolute and relative differences for each curve/baseline pair that
        failed the comparison.
        """
        name1 = kernel + ('-%03d-' % self.pairID)
        name2 = 'curves-' + type + '-%s_%s_VS_%s_%s.png' % ( self.version, self.name,
                                                             curve2.version, curve2.name)

        data_file_name = name1 + 'data' + name2
        dataPlot = os.path.join(dir, data_file_name)
        dataTitle = "Pair %i of %i: Actual Data Curves" %(self.pairID,numPairs)

        ## relative difference curve
        rel_file_name = name1 + 'rel_diff' + name2
        relPlot = os.path.join(dir,rel_file_name)
        relTitle= "Pair %i of %i: Relative Difference Curve" %(self.pairID,numPairs)

        ## absolute difference curve
        abs_file_name = name1 + 'abs_diff' + name2 
        absPlot = os.path.join(dir, abs_file_name)
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
                 verbose=True, use_and=False, absTol=-1.0, relTol=-1.0):
        
        self.base_file_name = base_file_name
        self.new_file_name  = new_file_name
        self.verbose        = verbose
        self.use_and        = use_and
        self.absTol         = absTol
        self.relTol         = relTol
        
        self.curves = reader(self.new_file_name, self.absTol, self.relTol)
        if verbose:
            print "%i curves read in" % len(self.curves)
            
        self.baselines = reader(self.base_file_name, self.absTol, self.relTol)
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


    def outputPlots(self, gnuplot, dir, kernel, type, xaxis, yaxis):
        """
        uses the data stored in curves and baselines to construct and execute
        gnuplot commands, generating .png files depicting original data,
        absolute and relative differences for each curve/baseline pair that
        failed the comparison.
        """
        pixels = {'small':'512,384', 'medium':'800,600', 'large':'1280,960'}

        numPairs = max(len(self.curves),len(self.baselines))

        ## open gnuplot just the once
        gp_proc = Popen( gnuplot+" -persist", shell=True, stdin=PIPE)
        gp = gp_proc.stdin

        failed_curves = [ c for c in self.curves.values() if c.failed ]

        gp.write( "set xlabel \"%s\"\n" % xaxis)
        gp.write( "set ylabel \"%s\"\n" % yaxis)
        gp.write( "set grid\n")
        gp.write( 'set key left Left reverse box font "Sans,8"\n')
        gp.write( "set term png size %s\n" % pixels[type] )

        for c in failed_curves:
            c.createOutputPlots(gp, self.baselines[c.name], numPairs, type, dir, kernel)

        gp.close()
        if gp_proc.wait() != 0:
            print "Errors creating plot files!"

###########################################################################################3

class UltraCheckBase:
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
    (self.options, self.inputFiles) = parser.parse_args(sys.argv[1:])

    if   (self.options.kernel == ""): 
        print "UltraCheck105 --kernel=xxx not specified"
        sys.exit(-1)
    elif (self.options.curvefile_baseline == ""): 
        print "UltraCheck105 --curvefile_baseline=xxx not specified"
        sys.exit(-1)
    elif (self.options.curvefile == ""): 
        print "UltraCheck105 --curvefile=xxx not specified"
        sys.exit(-1)

    if self.options.directory:
      # Go to directory with files to be compared
      os.chdir(self.options.directory)
      
    # ---------------------------------------------------------------------------------------------
    # Verify both curve files exist
    # ---------------------------------------------------------------------------------------------
    if not os.path.isfile(self.options.curvefile_baseline):
        print "Bypassing check, curvefile_baseline %s does not exist" % self.options.curvefile_baseline
        sys.exit(-1)

    if not os.path.isfile(self.options.curvefile):
        print "Bypassing check, curvefile %s does not exist" % self.options.curvefile
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
                                             relTol=self.options.rel_override)
    
    if comparator.comparecurves():
        ## if significant differences exist, output info and then exit with code 1
        outdir = '.'

        comparator.outputDiffInfo(outdir, self.options.kernel)
        comparator.outputJavaScriptCurves( outdir, self.options.kernel)
        
        if self.options.gnuplot:
            xaxis = "time (micro sec)"
            yaxis = "value"

            comparator.outputPlots(self.options.gnuplot, outdir, self.options.kernel,
                                   'small', xaxis, yaxis)
            comparator.outputPlots(self.options.gnuplot, outdir, self.options.kernel,
                                   'large', xaxis, yaxis)

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
            xaxis = "time (micro sec)"
            yaxis = "value"

            comparator.outputPlots(options.gnuplot, outdir, kernel,'small', xaxis, yaxis)
            comparator.outputPlots(options.gnuplot, outdir, kernel,'large', xaxis, yaxis)

        sys.exit(1)
    else:
        sys.exit(0)



    

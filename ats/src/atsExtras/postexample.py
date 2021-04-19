"""Script to run ats, then print stats
   Usage: python postexample.py [options] testfiles
"""
import ats, sys
manager = ats.manager
stats = {}
for status in ats.statuses.values():
    stats[status.name] = 0

def myReport(manager):
    N = max(1, float(len(manager.testlist)))
    for t in manager.testlist:
        stats[t.status.name] += 1
    for s in stats.keys():
        print s, "%6.2f%%" % (100.*stats[s]/N)

if __name__ == "__main__":
    manager.onExit(myReport)
    manager.main()

    
    



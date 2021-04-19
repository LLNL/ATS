#!/usr/apps/ats/7.0.0/bin/python
import sys
import ats

def main():
    result = ats.manager.main()
    sys.exit(result)

if __name__ == '__main__':
    main()

"""
'python -m ats' module entry point to run via 'python -m'
"""
import sys

import ats

def main():
    result = ats.manager.main()
    if result:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

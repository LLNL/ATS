"""
'python -m ats' module entry point to run via 'python -m'
"""
import sys

import ats

def main():
    result = ats.manager.main()

    # Return values need to be modified because code returns bool checking for errors
    # if there was no error then we return False, but codes using us expect 0 as a successful run
    if result:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

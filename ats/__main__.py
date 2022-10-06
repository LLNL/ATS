"""
'python -m ats' module entry point to run via 'python -m'
"""
import sys

import ats

def main():
    result = ats.manager.main()
    return result


if __name__ == "__main__":
    sys.exit(main())

import sys
import ats

def main():
    ats.manager.main()
    return_code = ats.manager._summary3()
    sys.exit(return_code)

if __name__ == '__main__':
    main()

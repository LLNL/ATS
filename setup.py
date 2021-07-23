from setuptools import find_packages, setup
from modulefinder import ModuleFinder


def get_version():
    finder = ModuleFinder()
    finder.run_script('version.py')
    from version import version as version_text
    return version_text


setup(
    name="ats",
    author="Shawn A. Dawson",
    author_email="dawson6@llnl.gov",
    url="https://github.com/LLNL/ATS",
    version=get_version(),
    description="Automated Testing System",
    install_requires=['numpy'],
    packages=['ats', 'ats.bin', 'ats.atsMachines', 'ats.util'],
    entry_points={
        'console_scripts': [
            'ats=ats.bin._ats:main',
            'ats3=ats.bin._ats3:main',
            'atslite1=ats.bin.atslite1:main',
            'atslite3=ats.bin.atslite3:main'
        ]
    }
)

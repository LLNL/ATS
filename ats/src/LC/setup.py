from setuptools import setup

setup(
    name="atsLC",
    author="Shawn Dawson",
    author_email="dawson6@llnl.gov",
    url="http://no.name.org",
    version='5.9.95',
    description="Automated Testing System LC addons",
    packages = ['atsMachines'],
    install_requires=['ats>=5.9.103'],
    entry_points={
        'console_scripts': ['atsWrap=atsWrap:main']
    },
)

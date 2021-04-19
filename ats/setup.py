import glob
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
    url="http://computation.llnl.gov/research/mission-support/WCI/automated-testing-system",
    version=get_version(),
    description="Automated Testing System",
    install_requires=['numpy <= 1.16.5'],
    package_dir={'': 'src'},
    packages=find_packages(
        where='src',
        exclude=['ats.charts', 'ats.database', 'LC']
    ),
    data_files=[
        ('atsASC/Visit/visit_testing/report_templates/css',       glob.glob('Extras/ASC/Visit/visit_testing/report_templates/css/*')),
        ('atsASC/Visit/visit_testing/report_templates/js',        glob.glob('Extras/ASC/Visit/visit_testing/report_templates/js/*')),
        ('atsASC/Visit/visit_testing/report_templates',           glob.glob('Extras/ASC/Visit/visit_testing/report_templates/*.html')),
        ('atsASC/Visit/visit_testing',                            glob.glob('Extras/ASC/Visit/visit_testing/*.pnm')),
        ('atsASC/Visit/visit_testing',                            glob.glob('Extras/ASC/Visit/visit_testing/*.txt')),
        ('atsASC/Visit/Example/baseline/category/example_script', glob.glob('Extras/ASC/Visit/Example/baseline/category/example_script/*')),
        ('atsASC/Visit/Example/data',                             glob.glob('Extras/ASC/Visit/Example/data/*')),
        ('atsASC/Visit/Example/tests/category',                   glob.glob('Extras/ASC/Visit/Example/tests/category/*')),
        ('atsASC/HelloATS',                                       glob.glob('Examples/HelloATS/*')),
        ('atsASC/HelloGPU',                                       glob.glob('Examples/HelloGPU/*')),
    ],
    entry_points={
        'console_scripts': [
            'ats=ats.bin._ats:main',
            'ats3=ats.bin._ats3:main',
            'atslite1=ats.bin.atslite1:main',
            'atslite3=ats.bin.atslite3:main'
        ]
    },
)

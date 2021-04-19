To install Sphinx, download and install "setuptools" using your python.
(That is, the python you want to install it into should be first in your path,
and you chmod +x the .egg file you downloaded and then run it).

Then easy_install -U Sphinx.

You'll need a latex installation to make pdfs with the make latexpdf target.
To make the web manual use make html.
To make a decently formatted text version use make text.

Note that beginning with version 5.4, the documentation can be built only if 
ats has been installed so that Sphinx can auto-document the modules.  If you 
cannot manage this for some reason, remove 'appendix.rst' from the index.rst file.



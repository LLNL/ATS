/usr/gapps/ats/scripts/replace 7.0.. 7.1.0 \
ats/bin/_ats.py \
ats/bin/_ats3.py \
ats/bin/atslite1.py \
ats/bin/atslite3.py \
test/HelloGPU/READ.ME \
test/HelloGPU/test.ats \

/usr/gapps/ats/scripts/replace "ATS_PATCH = ." "ATS_PATCH = 0" ats/version.py

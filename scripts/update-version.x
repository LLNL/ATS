/usr/gapps/ats/scripts/replace 7.0.. 7.0.6 \
ats/src/ats/bin/_ats.py \
ats/src/ats/bin/_ats3.py \
ats/src/ats/bin/atslite1.py \
ats/src/ats/bin/atslite3.py \
test/HelloATS/ats_check_log.py \
test/HelloATS/ats_hello \
test/HelloATS/create_test_ats.py \
test/HelloGPU/READ.ME \
test/HelloGPU/test.ats 

/usr/gapps/ats/scripts/replace "ATS_PATCH = ." "ATS_PATCH = 6" ats/src/ats/version.py

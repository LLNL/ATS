/usr/gapps/ats/scripts/replace 7.1.. 8.0.0 \
setup.cfg \
ats/bin/_ats.py \
ats/bin/_ats3.py \
ats/bin/atslite1.py \
ats/bin/atslite3.py \
test/HelloATS/ats_check_log.py \
test/HelloATS/ats_hello \
test/HelloATS/create_test_ats.py \
test/HelloGPU/READ.ME \
test/HelloGPU/test.ats \

/usr/gapps/ats/scripts/replace "ATS_PATCH = ." "ATS_PATCH = 1" ats/version.py


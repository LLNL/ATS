__author__ = 'reynolds12'

import MySQLdb
from _mysql_exceptions import *

db = MySQLdb.connect(
    host="bugzi",
    user="tracker",
    passwd="tracker",
    db="tracker")
cur = db.cursor()
#cur.execute("SELECT * FROM tables")
#cur.execute("SELECT * FROM user")
cur.execute(
"""SELECT
run.runDate       AS "Run Date   Time",
host.hostName     AS "Host",
user.userName     AS "User",
run.procs         AS "Nodes",
run.threads       AS "Cores",
run.wallTime      AS "Secs",
intv.entry        AS "Tests"
FROM run
LEFT JOIN code                   ON code.codeID=run.codeID
LEFT JOIN host                   ON host.hostID=run.hostID
LEFT JOIN user                   ON user.userID=run.userID
LEFT JOIN intproperty AS tempint ON tempint.runID=run.runID
LEFT JOIN property    AS intp    ON intp.propID=tempint.propID
LEFT JOIN intproperty AS intv    ON intv.runID=run.runID
                                and intp.propName="Tests"
WHERE code.codeName="ats"
GROUP BY user.userName, run.runDate
""")

col_names = []
for column in cur.description:
    col_names.append (column[0])

while True:
    row = cur.fetchone()
    if row == None:
        break
    print (str(row))
    line=''
    for col_num in range (len(col_names)):
        line = line + col_names[col_num] + ' : ' + str(row[col_num])
        if col_num < len(col_names):
            line = line + ', '
    print(line)
print ("")
print (repr(cur))
print (str(cur.__dict__.keys()).replace(',',',\n'))
# Produces:
#['_result',
# 'description',
# 'rownumber',
# 'messages',
# '_executed',
# 'errorhandler',
# 'rowcount',
# 'connection',
# 'description_flags',
# 'arraysize',
# '_info',
# 'lastrowid',
# '_last_executed',
# '_warnings',
# '_rows']
print (str(cur.__dict__).replace('), ', '),\n'))

print (col_names)
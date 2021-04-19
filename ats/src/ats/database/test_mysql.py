__author__ = 'reynolds12'

import mysql.connector
from mysql.connector import errorcode

config = dict(
    host='bugzi',
    user='tracker',
    password='tracker',
    database='tracker')
#try:
cnx = mysql.connector.connect(**config)
#except mysql.connector.Error as err:
#    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
#        print("Something is wrong with your user name or password")
#    elif err.errno == errorcode.ER_BAD_DB_ERROR:
#        print("Database does not exist")
#    else:
#        print(err)


cur = cnx.cursor()
query = """SELECT
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
    """
#cur.execute('SELECT * FROM tables')
#cur.execute('SELECT * FROM user')
cur.execute(query)

for row in cur.fetchall():
    print (row)

cnx.close()

# Parameters:
SET @start_date      := "2015-01-01";
SET @end_date        := "2015-12-31";
SET @user            := "all";

SET @end_date_time   := concat(@end_date, " 23:59:59");
SET @start_date_time := concat(@start_date, " 00:00:00");
# Returns total runtime seconds and total tests, grouped by host within week,
# with subtotals by week and overall totals.
SELECT 
# Be sure that the second parameter of [year]week(date, mode) matches: 
# the weekday named in str_to_date AND %x%v vs. %X%V, below!
str_to_date(concat(yearweek(run.rundate, 3), ' Monday'), '%x%v %W') AS "Week Starting",
host.hostName   AS "Host",
round(sum(run.wallTime),1) AS "Total Secs", 
sum(intv.entry) AS "Total Tests"
FROM run

LEFT JOIN code ON code.codeID=run.codeID
LEFT JOIN host ON host.hostID=run.hostID
LEFT JOIN user ON user.userID=run.userID
# intproperty points at property record.
# Need to get a temp intproperty record first so we can check the 
# propName of the associated property record and decide if we
# want the value (intproperty.entry) after all:
LEFT JOIN intproperty AS tempint ON tempint.runID=run.runID 
LEFT JOIN property    AS intp    ON intp.propID=tempint.propID
LEFT JOIN intproperty AS intv    ON intv.runID=run.runID
                                and intp.propName="Tests"
WHERE code.codeName = "ats" 
AND run.runDate BETWEEN @start_date_time AND @end_date_time
AND @user = "all" OR user.userName = @user 
GROUP BY `Week Starting`, `Host` WITH ROLLUP
;

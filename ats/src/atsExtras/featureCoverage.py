"""Script to run ats, storing results in a database"""
dbname = 'results'
masterFeatureList = "masterFeatureList"

import ats
manager = ats.manager.manager
from ats.times import datetime
try:
    import gadfly
except ImportError:
    print ("Gadfly database is not installed, feature coverage disabled.")
    raise SystemExit, 1

class resultsDatabase (object):
    "Provides a database interface to SnakeSQL.  Used for storing results from an ats run into a database."
    
    def __init__ (self, dbpath, dbname = "results"):
        "Creates interface to a new or existing database."

        import os, time, sys
        from ats.configuration import SYS_TYPE

        if dbpath == None:
            print "No database name supplied."
            sys.exit(1)

        self.__dbname = dbname
        self.__dbpath = dbpath
        self.__connectionOpen = False
        self.__usingExistingDatabase = None

        "Error log"
        self.errors = []

        try:
            self.__connection = gadfly.gadfly(self.__dbname, self.__dbpath)
            print "Selected database '%s'" % (self.__dbpath)
            self.__usingExistingDatabase = True;

        #If no database supplied, create one.
        except IOError:
            if (os.path.isdir(self.__dbpath) == False):
                os.mkdir(self.__dbpath)
            self.__connection = gadfly.gadfly()
            self.__connection.startup(self.__dbname, self.__dbpath)

            cursor = self.__connection.cursor()

            #Note - primary keys and foreign keys not supported by gadfly.
            #Using indexes to get same effect as primary keys when needed.

            cursor.execute("CREATE TABLE tests \
                            (name varchar, \
                            startDateTime integer, \
                            endDateTime integer, \
                            system varchar, \
                            path varchar, \
                            status varchar, \
                            np integer, \
                            mesh varchar)")

            cursor.execute("CREATE UNIQUE INDEX tests_pkeys on tests(name, startDateTime, system)")

            cursor.execute("CREATE TABLE features \
                            (name varchar, \
                            mesh varchar, \
                            tier varchar )")

            cursor.execute("CREATE UNIQUE INDEX features_pkeys on features(name, mesh)")

            cursor.execute("CREATE TABLE loggedFeatures \
                            (test varchar, \
                            feature varchar, \
                            mesh varchar)")

            self.__connection.commit()
            print "Database " + self.__dbpath + " created."
            self.__usingExistingDatabase = False

        self.__connectionOpen = True

    """Imports a feature list into the database.  If a feature table already exists, it will be
       overwritten with the new feature list"""
    def importFeatures(self, featureList):
        from gadfly import store
        import sys 

        try:
            file = open(featureList)
            print "Reading in '%s'..." % featureList
        except IOError:
            return
 
        if self.__connectionOpen == True:
            cursor= self.__connection.cursor()
            tier = ''

            #if using existing database, delete old feature list, will be importing the new one.
            if self.__usingExistingDatabase:
                sql = "DELETE from features"
                cursor.execute(sql)

            for line in file:
                line = line.rstrip('\n')
                #Skip blank lines
                if line:
                    #Emulate the 'stick' command to make things familiar for the user
                    if line.startswith('stick('):
                        if line[6:].startswith('tier='):
                            tier=line[11:-1]
                        else:
                            print "Unsupported variable in stick."
                            print "Valid syntax is stick(tier=X)"
                    #Skip comments
                    elif line.startswith('#'):
                        continue
                    #Feature entry
                    else:
                        #check for mesh dependecy 'feature<meshtype>'
                        #poor man's match. Could also use a regex match on .*<.*>
                        mesh = ""
                        subline = line.split("<");
                        if line.endswith("<all>"):
                            line = line[:-5]
                            meshtypes = ["polygonal", "polygonalrz", "polyhedral"]
                            for mesh in meshtypes:
                                sql = "INSERT into features (name, mesh, tier) VALUES ('%s', '%s', '%s')" \
                                    % (line, mesh, tier)
                                try:
                                    cursor.execute(sql)
                                except store.StorageError, e:
                                    print "Couldn't import feature: " + line + " into database's feature list."
                                    print "Verify no duplicate entries in the master feature list."
                                    print "SQL Error was: ", e
                                    sys.exit(1)
                        else:
                            if line.endswith("<polygonal>"):
                                mesh = "polygonal"
                                line = line[:-11]
                            elif line.endswith("<polyhedral>"):
                                mesh = "polyhedral"
                                line = line[:-12]
                            elif line.endswith("<polygonalrz>"):
                                mesh = "polygonalrz"
                                line = line[:-13]

                            sql = "INSERT into features (name, mesh, tier) VALUES ('%s', '%s', '%s')" \
                               % (line, mesh, tier)
                            try:
                                cursor.execute(sql)
                            except store.StorageError, e:
                                print "Couldn't import feature: " + line + " into database's feature list."
                                print "Verify no duplicate entries in the master feature list."
                                print "SQL Error was: ", e
                                sys.exit(1)
            
            self.__connection.commit()
        else:
            print "No database connection exists."

    "Inserts a test entry into the database"
    def insert(self, test):
        import time, datetime

        if self.__connectionOpen == True:
            cursor= self.__connection.cursor()

        # ATS and BATS use different names for some of the test attributes.
        # They also format the date time strings different (YY/MM/DD vs YY-MM-DD)
        # Next step is to standardize the test objects and some of the data types.
        try:
            name = test.name
            path = test.directory
            system = test.system
            np = int(test.np)
            startDateTime = datetime.datetime(*time.strptime(test.startDateTime, "%Y-%m-%d %H:%M:%S")[0:6])
            if test.endDateTime:
                endDateTime = datetime.datetime(*time.strptime(test.endDateTime, "%Y-%m-%d %H:%M:%S")[0:6])
            else:
                endDateTime = startDateTime

        except AttributeError:
            name = test.testlabel
            path = test.directory
            system = test.platform
            np = int(test.nprocs)
            startDateTime = datetime.datetime(*time.strptime(test.startDateTime, "%Y/%m/%d %H:%M:%S")[0:6])
            if test.endDateTime:
                endDateTime = datetime.datetime(*time.strptime(test.endDateTime, "%Y/%m/%d %H:%M:%S")[0:6])
            else:
                endDateTime = startDateTime
      
        #Currently only support one entry in 'systems'
        #Need to add separate table with 'test' and 'system' field to support a list
        #type with multiple entries
        sql = "INSERT INTO tests \
               (name, startDateTime, endDateTime, system, path, status, np, mesh) \
               VALUES ('%s', '%s', '%s', '%s', '%s', '%s', %u, '%s')" % \
               (name, startDateTime, endDateTime, system, path, test.status, np, test.mesh)

        cursor.execute(sql)

        for entry in test.loggedFeatures:
            if (entry.endswith("<mesh>")):
                mesh = test.mesh
                entry = entry.split('<')[0]
            else:
               mesh = ''

            #gadfly db doesn't support foreign keys unfortunetly, so manually
            #verify that feature exists in features table before adding to
            #logged features.
            sql = "SELECT name, mesh from features WHERE name = '%s' AND mesh = '%s'" \
                  % (entry, mesh)
            cursor.execute(sql)
            results = cursor.fetchall()
            if len(results) == 0:
                line = "From test: %s, feature '%s" % (name, entry)
                if mesh != '':
                    line = line + "<%s>" % mesh
                line = line + "' missing from master feature list."
                self.errors.append(line)
            else:
                sql = "INSERT INTO loggedFeatures (feature, test, mesh) VALUES ('%s','%s','%s')" % (entry, name, mesh)
                cursor.execute(sql)
 
        self.__connection.commit()

    "Close the database connection."
    def close(self):
        if self.__connectionOpen == True:
            if len(self.errors) != 0:
                print "-------------------------------------------------"
                print "Database errors"
                print "-------------------------------------------------"
                for entry in self.errors:
                    print entry
            self.__connection.close()
            self.__connection = False

if __name__ == "__main__":
    resultsDB = resultsDatabase.resultsDatabase()
    resultsDB.importFeatures("masterFeatureList")
    def writeDatabase(manager):
        for t in manager.testlist:
            resultsDB.insert(test)
    manager.onExit(writeDatabase)
    manager.main(sys.argv[1])
    results.DB.close()
    



#!/usr/bin/python
import mysql.connector
import couchdb, sys
from funcs import *

conn = mysql.connector.connect(user = 'DBUsername', password = 'DBPassword', host = 'localhost', database = 'nomie')
c = conn.cursor()

couch = couchdb.Server('CouchDBServer')


t = couch['nomieuser_trackers']
e = couch['nomieuser_events']

if __name__ == "__main__":
	if len(sys.argv) == 1:	## Default way to run the script
		epoch, couchDbID = getMostRecentMySQLEvent(c)
		newEvents = getNewEvents(c, e, epoch, couchDbID)
		insertNewEvents(c, conn, newEvents, e)
		conn.commit()
	elif str(sys.argv[1]) == 'allTrackers':
		insertAllTrackers(c, t) 
		conn.commit()
	elif str(sys.argv[1]) == 'allEvents':
		insertAllEvents(c, conn, e)
		conn.commit()
	elif str(sys.argv[1]) == 'createTables':
		createTables(c, conn)
		conn.commit()

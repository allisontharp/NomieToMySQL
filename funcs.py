import mysql.connector, couchdb
from datetime import datetime as dt
from datetime import timedelta
import time

def getTrackerInfo(dbt):
	name = dbt['label']
	try:
		minAmt = dbt['config']['min']
	except:
		minAmt = 'NULL'
	try:
		maxAmt = dbt['config']['max']
	except:
		maxAmt = 'NULL'
	
	defaultCharge = dbt['charge']
	couchDbID = dbt['_id']
	
	return name, minAmt, maxAmt, defaultCharge, couchDbID

def getChargeFunc(dbt):
	try:
		cond = [i['cond'] for i in dbt['config']['chargeFunc']]
		compare = [i['compare'] for i in dbt['config']['chargeFunc']]
		charge = [i['charge'] for i in dbt['config']['chargeFunc']]
	except:
		cond = 'None'
		compare = 0
		charge = []	
	
	print cond
	print compare
	print charge
	return cond, compare, charge




def getChargeIDs(c, dbt):
	[cond, compare, charge] = getChargeFunc(dbt)
	condID = [getConditionID(c, i) for i in cond]
	i = 0
	chargeIDs = []
	print condID
	print compare
	print charge
	if len(charge) > 0:
		for con in condID:
			a = insertCharges(c, condID[i], compare[i], charge[i])
			chargeIDs.append(a)
			i += 1
	return chargeIDs


def getConditionID(c, cond):
	query = "SELECT conditionID FROM conditions WHERE name like '{nm}'"
	c.execute(query.format(nm = cond))
	conditionID = c.fetchall()

	

	if conditionID == []:
		query = "INSERT INTO conditions (name) VALUES ('{nm}')"
		c.execute(query.format(nm = cond))
		query = "SELECT last_insert_id()"
		c.execute(query)
		conditionID = c.fetchall()

	conditionID = conditionID[0][0]
	print 'conditionID'
	print conditionID
	return conditionID


def insertCharges(c, condID, compare, value):
	query = "INSERT INTO charges (conditionID, compare, value) VALUES ({cid}, {cp}, {vl})"
	print query.format(cid = condID, cp = compare, vl = value)
	c.execute(query.format(cid = condID, cp = compare, vl = value))
	query = "SELECT last_insert_id()"
	c.execute(query)
	chargeID = c.fetchall()[0][0]
	return chargeID

def insertTrackerCharge(c, trackerID, chargeID):
	query = "INSERT INTO trackerCharges (trackerID, chargeID) VALUES ({tid}, {cid})"
	print trackerID, chargeID
	print query.format(tid = trackerID, cid = chargeID)
	c.execute(query.format(tid = trackerID, cid = chargeID))

def insertTracker(c, name, minAmt, maxAmt, defaultCharge, couchDbID, chargeIDs):
	query = "INSERT INTO trackers (name, min, max, defaultCharge, couchdbid) VALUES ('{nm}', {mn}, {mx}, {ps}, '{ch}')"
	
	print query.format(nm=name, mn = minAmt, mx = maxAmt, ps = defaultCharge, ch = couchDbID)
	try:
		c.execute(query.format(nm=name, mn = minAmt, mx = maxAmt, ps = defaultCharge, ch = couchDbID))
		query = "SELECT last_insert_ID()"
		c.execute(query)
		trackerID = c.fetchall()[0][0]
		if len(chargeIDs) > 0:
			print chargeIDs
			for charge in chargeIDs:
				insertTrackerCharge(c, trackerID, charge)
	except (mysql.connector.errors.IntegrityError) as e:
		print name + " already exists in the tracker table."


def insertAllTrackers(c, db):
	for trackers in db:
		tracker = db[trackers]
        	[name, minAmt, maxAmt, defaultCharge, couchDbID] = getTrackerInfo(tracker)
		chargeIDs = getChargeIDs(c, tracker)
		
		insertTracker(c, name, minAmt, maxAmt, defaultCharge, couchDbID, chargeIDs)


def trackerDictInit(c):
	query = "SELECT couchDbID, trackerID FROM trackers"
	c.execute(query)
	out = c.fetchall()
	return dict(out)

def getEventType(dbt):
	couchID = dbt['_id']
	idArray = couchID.split('|')
	idType = str(idArray[1])
	
	return idArray, idType

def getEventInfo(dbt, idArray, c, conn):
	trackerIDdict = trackerDictInit(c)
	
	epochTime = int(idArray[2])/1000.0
	couchDbID = str(idArray[3])	

	try:	
		trackerID = trackerIDdict[couchDbID]
	except (KeyError) as e:
		chargeIDs = getChargeIDs(c, dbt)
		insertTracker(c, couchDbID, 0, 0, 0, couchDbID, chargeIDs)
		conn.commit()
		print couchDbID
		trackerID = trackerIDdict[couchDbID]
	
	eventTime =  dt.fromtimestamp(epochTime) #- timedelta(hours=4)
	eventTime = eventTime.strftime('%Y-%m-%d %H:%M:%S')
	
	print trackerID, eventTime

	try:
		lat = dbt['geo'][0]
		lng = dbt['geo'][1]
	except (IndexError) as e:
		lat = 0
		lng = 0	

	value = dbt['value']

	return trackerID, lat, lng, eventTime, value

def insertEvent(c, trackerID, lat, lng, date, value):
	query = "INSERT INTO events (trackerID, lat, lng, date, value) VALUES ({tid}, {lt}, {ln}, '{dt}', '{vl}')"

	print query.format(tid = trackerID, lt = lat, ln = lng, dt = date, vl = value)
	try:
		c.execute(query.format(tid = trackerID, lt = lat, ln = lng, dt = date, vl = value))
	except (mysql.connector.errors.IntegrityError) as e:
		print 'Duplicate entry for this record'

def insertAllEvents(c, conn, db):
	for events in db:
		event = db[events]
		if event['_id'].startswith('_design'):
			print 'Skipping design docs'
		elif event['_id'].startswith('note'):
			print 'Skipping notes'
		else:
			idArray, eventType = getEventType(event)
			print eventType
			if eventType == 'tm':
				[trackerID, lat, lng, eventTime, value] = getEventInfo(event, idArray, c, conn)
				print trackerID, lat, lng, eventTime, value
				insertEvent(c, trackerID, lat, lng, eventTime, value)

def getMostRecentMySQLEvent(c):
	query = """select e.eventID, e.trackerID, e.date, t.couchDbID FROM events e INNER JOIN trackers t ON t.trackerID = e.trackerID ORDER BY e.date desc LIMIT 1"""

	c.execute(query)
	out = c.fetchall()

	d = out[0][2] + timedelta(hours=4)

	epoch = (d - dt(1970,1,1)).total_seconds()
	couchDbID = out[0][3]
	return epoch, couchDbID
	
def getNewEvents(c, db, epoch, couchDbID):
	noDesign = [a for a in db if not(a.startswith('_design'))]
	noNotes = [a for a in noDesign if not(a.startswith('note'))]
	
	splitEvents = [a.split('|') for a in noNotes]

	tmEvents = [a for a in splitEvents if a[1] == 'tm']

	
	newEvents = [a for a in tmEvents if (int(a[2]))/1000 >= (epoch + 1000)]
	
	return newEvents

def insertNewEvents(c, conn, events, db):
	for event in events:
		e = db["|".join(event)]
		[trackerID, lat, lng, eventTime, value] = getEventInfo(e, event, c, conn)
		insertEvent(c, trackerID, lat, lng, eventTime, value)

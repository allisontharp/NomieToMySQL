## NomieToMySQL
These python scripts are used to convert the Nomie couchDB documents into a MySQL relational database.  After the database is created and populated, you can use tools like PowerBI or Grafana to visualize the data by connecting to the new db.
###### Dependencies
- [Nomie CouchDB sync](https://docs.nomie.io/development/couchdb-setup.html)
- MySQL 
- Python Modules
- - mysql.connector
- - couchdb

###### Initialize MySQL database
```
main.py createTables
```
###### Add all trackers to the database
```
main.py allTrackers
```
###### Add all events to the database
```
main.py allEvents
```
###### Add most recent missing events
```
main.py
```

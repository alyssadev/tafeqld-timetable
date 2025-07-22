tafeqld-timetable
=================

A flask service that I use to convert my tafeqld timetable to a .ics file for import into Outlook

Demo instance (uptime not guaranteed!): https://tqld-timetable.aly.pet/ (404 because currently no index page or UI for non-tech users, check [flask/app.py](flask/app.py))

Usage (before UI is developed)
------------------------------

* Identify your tafe region:

```json
{"Brisbane": "TQBN", "East Coast": "TQEC", "Gold Coast": "TQGC", "North": "TQNT", "South West": "TQSW"}
```

* Get your search query from https://timetables.tafeqld.edu.au/Group e.g `ict50220`
* Navigate to e.g `/search?region=TQBN&group=ict50220`. If the search term matches more than one course, it will return json indicating this and list the results. Otherwise it will redirect to the first result.
* Results will have a hash property. This can be used in `/<hash>/timetable.ics`. Hashes can be abbreviated.
  * e.g `/f273d9f/timetable.ics` is shorthand for getting f273d9f94cc26573fea21639fae66ab3f48af1a7/timetable.ics, as long as there is no collision
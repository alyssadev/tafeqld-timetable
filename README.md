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
* Navigate to e.g /timetable.ics?region=TQBN&group=ict50220 . If the search term matches more than one course, it will return json indicating this and list the results
  * Currently, the results are accompanied by a `n` argument, this can be used to limit the results down to that argument. This is a temporary fix for a bug and is already deprecated. However, it's currently critical to functionality. I'm recovering from a cold, sue me.
* Navigate to e.g /timetable.ics?region=TQBN&group=ict50220&n=10 . This will download the specific timetable required.

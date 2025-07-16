from requests import get
from time import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as Soup
from flask import Flask, jsonify, request, make_response
from urllib.parse import quote_plus

app = Flask(__name__)

regions = {"Brisbane": "TQBN", "East Coast": "TQEC", "Gold Coast": "TQGC", "North": "TQNT", "South West": "TQSW"}
ts = lambda: int(time()*1000)

def search(region, term):
    return get("https://timetables.tafeqld.edu.au/Group/SearchGroup", params={"searchStr": term, "database": regions[region] if region in regions else regions["Brisbane"], "_": ts()}).json()

def week(group):
    return get("https://timetables.tafeqld.edu.au/Group/WeekTable", params={"group": group, "weekNo": 0, "func": "SelectGroup", "_": ts()}).json()["weekNo"]

def timetable(group, weekNo):
    page = Soup(get("https://timetables.tafeqld.edu.au/Group/GroupTable", params={"id": group, "week": weekNo, "duration": 10000, "_": ts()}).text, features="html.parser")
    events = []
    current_date = None
    for row in page.find_all("tr"):
        if "class" in row.attrs and "group-header" in row["class"]:
            current_date = datetime.strptime(row.find("span").string, "%A, %B %d, %Y")
            continue
        times = [i+"M" for i in row.find("p").string.strip().replace(" - ", "").split("M")[:2]]
        start, end = map(lambda i: datetime.combine(current_date, datetime.strptime(("0"+i) if len(i) == 6 else i, "%I:%M%p").time()), times)
        location = row.find("a")
        if location:
            geo = location["href"].split("=")[-1]
            location = location.string
        else:
            geo = None
            location = " ".join(row.find("p").string.strip().split("M")[2:])
        units = row.find("td").contents[-1].string.strip().split(", ")
        events.append({"date": current_date, "start": start, "end": end, "location": location, "units": units, "geo": geo})
    return events

def calendar(events):
    outp = []
    dtstamp = (datetime.now() - timedelta(hours=10)).strftime("%Y%m%dT%H%M%SZ")
    for event in events:
        dtstart = (event["start"] - timedelta(hours=10)).strftime("%Y%m%dT%H%M%SZ")
        dtend = (event["end"] - timedelta(hours=10)).strftime("%Y%m%dT%H%M%SZ")
        uid = dtstamp + dtstart
        summary = event["location"]
        comment = ", ".join(event["units"])
        geo = event["geo"]
        outp.append(f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{summary}
COMMENT:{comment}
GEO:{geo}
END:VEVENT""")
    outp = "\n".join(outp)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//hacksw/handcal//NONSGML v1.0//EN
{outp}
END:VCALENDAR"""

@app.route("/timetable.ics")
def ics():
    if not "group" in request.args:
        return jsonify({"error": "No search term provided for argument 'group'"}), 400
    if not "region" in request.args:
        return jsonify({"error": "No search term provided for argument 'region'"}), 400
    results = search(request.args["region"], request.args["group"])
    if len(results) > 1:
        if "n" in request.args and request.args["n"].isdigit():
            results = [results[int(request.args["n"])]]
        else:
            results = [{"n": n, "ID": r["ID"], "Name": r["Name"]} for n,r in enumerate(results)]
            return jsonify({"error": "Please provide a more precise search term (ID field) for argument 'group'", "results": results}), 400
    group = results[0]["ID"]
    weekNo = week(group)
    events = timetable(group, weekNo)
    resp = make_response(calendar(events), 200)
    resp.headers["Content-Type"] = "text/calendar"
    #resp.headers["Content-Disposition"] = "inline"
    return resp

if __name__ == "__main__":
    app.run(port=53424, host="10.8.0.1")

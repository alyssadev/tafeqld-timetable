from requests import get
from time import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as Soup # type: ignore
from flask import Flask, jsonify, request, make_response, redirect, render_template
from urllib.parse import quote_plus
from hashlib import sha1

from redis import Redis
r = Redis(host='redis', port=6379, db=0)

def cache_hash(input: str):
    hash = sha1(input.encode("utf-8")).hexdigest()
    r.set(f"hash:{hash}", input)
    return hash

def resolve_hash_id(short_hash: str):
    prefix = f"hash:{short_hash}"
    cursor = 0 
    matches = []
    while True:
        cursor, keys = r.scan(cursor=cursor, match=prefix + "*", count=100)
        matches.extend(keys)
        if cursor == 0 or len(matches) > 1:
            break
    if len(matches) == 1:
        return r.get(matches[0]).decode()
    return None

app = Flask(__name__)

regions = {"Brisbane": "TQBN", "East Coast": "TQEC", "Gold Coast": "TQGC", "North": "TQNT", "South West": "TQSW"}
ts = lambda: int(time()*1000)

def search(region, term):
    results = get("https://timetables.tafeqld.edu.au/Group/SearchGroup", params={"searchStr": term, "database": regions[region] if region in regions else regions["Brisbane"], "_": ts()}).json()
    hashes = []
    for n,result in enumerate(results):
        hashes.append(cache_hash(result["ID"]))
    return results, hashes

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

def ics(group):
    weekNo = week(group)
    events = timetable(group, weekNo)
    resp = make_response(calendar(events), 200)
    resp.headers["Content-Type"] = "text/calendar"
    #resp.headers["Content-Disposition"] = "inline"
    return resp

@app.route("/<hash>/timetable.ics")
def ics_hash(hash):
    group = resolve_hash_id(hash)
    if not group:
        return jsonify({"error": "Key Not Found"}), 404
    return ics(group)

@app.route("/search")
def search_endpoint():
    if not "group" in request.args:
        return jsonify({"error": "No search term provided for argument 'group'"}), 400
    if not "region" in request.args:
        return jsonify({"error": "No search term provided for argument 'region'"}), 400
    results, hashes = search(request.args["region"], request.args["group"])
    if len(results) > 1:
        results = [{"ID": r["ID"], "Name": r["Name"], "hash": hashes[n]} for n,r in enumerate(results)]
        return jsonify({"results": results})
    return redirect(f"/{results[0]['hash']}/timetable.ics")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(port=53424, host="0.0.0.0")

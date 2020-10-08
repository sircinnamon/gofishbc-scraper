# https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start=9/1/2020&end=10/1/2020
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime,timedelta
import os, urllib

HISTORY_FILE = "history.json"
if "GOFISH_HISTORY_FILE" in os.environ:
	HISTORY_FILE = os.environ["GOFISH_HISTORY_FILE"]
PUSHBULLET_CHANNEL = "gofishbc"
BASE_URL = "https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start={}&end={}&region={}"
API_URL = "https://api.pushbullet.com/v2/pushes"
WEBPUSH_URL = "https://thor.sircinnamon.ca:10043"
REGIONS = [
	"Cariboo",
	"East Kootenay",
	"Lower Mainland",
	"Okanagan",
	"Omineca",
	"Peace",
	"Skeena",
	"Thompson-Nicola",
	"Vancouver Island",
	"West Kootenay"
]

def load_history():
	f = open(HISTORY_FILE, "r")
	hst = json.load(f)
	f.close()
	return hst

def save_history(hst):
	f = open(HISTORY_FILE, "w")
	json.dump(hst, f)
	f.close()

def hash_evt(evt):
	return hash(frozenset(evt.items()))

def get_all_events(startdate, enddate, hst):
	all_events = {
		"All": []
	}
	for region in REGIONS:
		url = BASE_URL.format(startdate, enddate, urllib.parse.quote(region.upper()))
		events = get_events(url)
		events = filter_seen_events(events, hst)
		all_events[region] = events
		all_events["All"] = all_events["All"] + events
	return all_events

def get_events(url):
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	try:
		table_rows = soup.find(id="report_table").find_all("tr")
	except AttributeError as e:
		return []
	stock_events = []
	del table_rows[0] # The header
	for tr in table_rows:
		contents = list(filter(lambda x: x != '\n', tr.contents))
		# print(contents)
		evt = {
			"date": str(contents[0].string),
			"waterbody": str(contents[1].string),
			"town": str(contents[2].string),
			"species": str(contents[3].string),
			"strain": str(contents[4].string),
			"genotype": str(contents[5].string),
			"stage": str(contents[6].string),
			"avg_size": str(contents[7].string),
			"quantity": str(contents[8].string)
		}
		stock_events.append(evt)
	return stock_events

def filter_seen_events(evt_list, history):
	def filter_func(x):
		date = x["date"]
		# Is this event in the hash list of seen events
		if not date in history: return True
		return not hash_evt(x) in history[date]
	return list(filter(filter_func, evt_list))

def notify_events(evt_list, start, end, region):
	# for e in evt_list:
	# 	print(e)
	# 	print(hash_evt(e))
	if len(evt_list) == 0: return
	# return create_pushbullet_notif(evt_list, start, end)
	return create_webpush_notif(evt_list, start, end, region)

def add_events_to_history(evt_list, history):
	for e in evt_list:
		if not e["date"] in history:
			history[e["date"]] = []
		history[e["date"]].append(hash_evt(e))
	return history

def format_date(date):
	return date.strftime("%Y/%m/%d")

def create_webpush_notif(events, start, end, region):
	t = region.lower().replace("-", "").replace(" ", "")
	headers = {
		"Content-Type":"application/json",
		"Authorization": "Bearer {}".format(os.environ["WEBPUSH_TOKEN"])
	}
	url = WEBPUSH_URL + "/notification"
	title = "New Fish Stocked{}!".format("" if region=="All" else (" In {}".format(region)))
	click_url = BASE_URL.format(start, end, urllib.parse.quote(region.upper()))
	body = {
		"type": t,
		"content": {
			"title": title,
			"body": format_push_body(events),
			"data": {"clickUrl": click_url}
		}
	}
	print(body)
	res = requests.post(url, json=body, headers=headers)
	if not res.ok:
		print(res.status_code)
	return res.ok

def format_push_body(events):
 out = ""
 for e in events:
 	line = "{} stocked in {}\n".format(e["species"].upper(), e["waterbody"])
 	out = out+line
 return out


enddate = format_date(datetime.now())
startdate = format_date(datetime.now() - timedelta(7))

print("Query from {} to {}".format(startdate, enddate))
hst = load_history()
evts = get_all_events(startdate, enddate, hst)
for region in evts.keys():
	print("Notify for region {} - {} evts".format(region, len(evts[region])))
	success = notify_events(evts[region], startdate, enddate, region)
	if success and region.lower() != "all":
		add_events_to_history(evts[region], hst)
save_history(hst)
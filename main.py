# https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start=9/1/2020&end=10/1/2020
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime,timedelta
import os

HISTORY_FILE = "history.json"
PUSHBULLET_CHANNEL = "gofishbc"
BASE_URL = "https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start={}&end={}"
API_URL = "https://api.pushbullet.com/v2/pushes"

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

def get_events(startdate, enddate):
	url = BASE_URL.format(startdate, enddate)
	page = requests.get(url)

	soup = BeautifulSoup(page.content, 'html.parser')
	table_rows = soup.find(id="report_table").find_all("tr")
	stock_events = []
	del table_rows[0] # The header
	for tr in table_rows:
		contents = list(filter(lambda x: x != '\n', tr.contents))
		# print(contents)
		evt = {
			"date": contents[0].string,
			"waterbody": contents[1].string,
			"town": contents[2].string,
			"species": contents[3].string,
			"strain": contents[4].string,
			"genotype": contents[5].string,
			"stage": contents[6].string,
			"avg_size": contents[7].string,
			"quantity": contents[8].string
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

def notify_events(evt_list, start, end):
	# for e in evt_list:
	# 	print(e)
	# 	print(hash_evt(e))
	if len(evt_list) == 0: return
	create_pushbullet_notif(evt_list, start, end)

def add_events_to_history(evt_list, history):
	for e in evt_list:
		if not e["date"] in history:
			history[e["date"]] = []
		history[e["date"]].append(hash_evt(e))
	return history

def format_date(date):
	return date.strftime("%Y/%m/%d")

def create_pushbullet_notif(events, start, end):
	push_data = {
		"type": "link",
		"url": BASE_URL.format(start, end),
		"body": format_push_body(events),
		"title": "New Fish Stocked!",
		"channel_tag": PUSHBULLET_CHANNEL
	}
	access_token = os.environ["PB_ACCESS_TOKEN"]
	api_url = API_URL
	headers = {
		"Content-Type":"application/json",
		"Access-Token": access_token
	}
	res = requests.post(api_url, json=push_data, headers=headers)
	if not res.ok:
		print(res.status_code())
		print(res.json())

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
evts = get_events(startdate, enddate)
print("{} total events found.".format(len(evts)))
evts = filter_seen_events(evts, hst)
print("{} unseen events found.".format(len(evts)))
success = notify_events(evts, startdate, enddate)
if success:
	add_events_to_history(evts, hst)
	save_history(hst)
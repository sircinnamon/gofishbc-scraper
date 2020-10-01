# https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start=9/1/2020&end=10/1/2020
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime,timedelta

HISTORY_FILE = "history.json"

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
	url = "https://www.gofishbc.com/Stocked-Fish/Detailed-Report.aspx?start={}&end={}".format(startdate, enddate)
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

def notify_events(evt_list):
	for e in evt_list:
		print(e)
		print(hash_evt(e))

def add_events_to_history(evt_list, history):
	for e in evt_list:
		if not e["date"] in history:
			history[e["date"]] = []
		history[e["date"]].append(hash_evt(e))
	return history

def format_date(date):
	return date.strftime("%Y/%m/%d")


enddate = format_date(datetime.now())
startdate = format_date(datetime.now() - timedelta(7))

print("Query from {} to {}".format(startdate, enddate))
hst = load_history()
evts = get_events(startdate, enddate)
print("{} total events found.".format(len(evts)))
evts = filter_seen_events(evts, hst)
print("{} unseen events found.".format(len(evts)))
notify_events(evts)
add_events_to_history(evts, hst)
save_history(hst)
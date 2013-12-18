import ConfigParser
import httplib, json, linecache, pywapi
import random, requests
import sys 
import string 
from bs4 import BeautifulSoup
from time import mktime, sleep, strptime
from datetime import datetime, timedelta

config = ConfigParser.ConfigParser()
config.read(sys.argv[1])

def jerkcity():
	lineno = int(random.random()*563)
	return linecache.getline("jerkcity.caps.txt", lineno)

def weather(msg):
	weather_zip = msg.split(" ")
	msg = "Invalid Input.  Valid Input is !weather <zipcode> <f or c>" 
	if len(weather_zip) > 1:
		weather = pywapi.get_weather_from_weather_com(weather_zip[1])
		if weather.get("error") is None:
			curr_cond = string.lower(weather['current_conditions']['text']).encode('utf-8')
			curr_temp = weather['current_conditions']['temperature'].encode('utf-8')
			form = 'c'
			if len(weather_zip) == 3 and weather_zip[2] == 'f':
				curr_temp = float(curr_temp)*9/5+32
				form = 'f'
			msg = "The weather at {zip} is {cond} and the temp is {temp}{form}".format(zip=weather_zip[1], cond=curr_cond, temp=int(curr_temp), form=form)
	return msg

def get_user(msg):
	user_info = msg.split(" ", 1)
	pw = config.get("other", "pw")
	link = config.get("other", "link")
	url="{link}{pw}&username={user}".format(link=link, pw=pw, user=user_info[1])
	soup = BeautifulSoup(requests.get(url).text)
	out_str = soup.text.replace(",", " |")
	return out_str.encode('utf-8', errors='ignore').strip()

class Seen():
	def __init__(self):
		self.seen_dict = {}

	def load_dict(self):
		try:
			with open('seen.json', 'r') as f:
				curr = json.load(f)
				if len(curr) > len(self.seen_dict):
					self.seen_dict = curr
		except ValueError:
			pass
		except IOError:
			pass 

	def update_dict(self, user, msg, time):
		user = user.split("!")[1]
		user = user.split("@")[0]
		self.seen_dict[user] = (time, msg)

	def store_dict(self):
		with open("seen.json", "w") as f:
			json.dump(self.seen_dict, f, sort_keys=True, indent=4, separators=(',', ': '))

	def get_seen(self, msg):
		seen = msg.split(" ")
		msg = "Invalid Input.  Valid Input is !seen <username>"
		if len(seen) >= 2:
			seen[1] = seen[1].split("^")[0]
			if self.seen_dict.get(seen[1]) is not None:
				when, said = self.seen_dict.get(seen[1])
				when = datetime.fromtimestamp(mktime(strptime(when[:-7], "%Y-%m-%d %H:%M:%S")))
				d = (datetime.utcnow() - when)
				minutes = d.seconds/60
				hours = minutes/60
				msg = "User {usr} was last seen {d} days, {h} hours, {m} minutes and {s} seconds ago - '{said}'".format(usr=seen[1], d=d.days, h=hours, m=minutes, s=d.seconds%60, said=said)
			else:
				msg = "I haven't seen that user =("
		return msg
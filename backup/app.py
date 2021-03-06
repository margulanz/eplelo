from flask import Flask,render_template,url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup,NavigableString
from dateutil import parser
from datetime import *
from flask_apscheduler import APScheduler
from sqlalchemy import or_

season = 2021


def elo_change(team_a,team_b,team_a_rank,team_b_rank,round,team_a_score,team_b_score):
	K = 40
	goal_dif = abs(team_a_score-team_b_score)
	if goal_dif == 1 or goal_dif == 0:
		G = 1
	elif goal_dif == 2:
		G = 3/2
	else:
		G = (11+goal_dif)/8


	if team_a_score > team_b_score:
		W = 1
	elif team_a_score < team_b_score:
		W = 0
	else:
		W = 0.5
	dr = team_a_rank - team_b_rank
	We = 1 / (10**(-dr/400)+1)

	# Change in rating
	P = K*G*(W - We)
	return P

def match_parser(season): # Yields each match of the giver season
	for match_round in range(1,39):
		url = f'https://www.worldfootball.net/schedule/eng-premier-league-{season}-spieltag/{match_round}/'
		response = requests.get(url)
		soup  = BeautifulSoup(response.text,'lxml')
		table = soup.find('table',class_ = 'standard_tabelle')
		match_date = ''

		for match in table:
			if isinstance(match, NavigableString):
				continue
			match_info = match.find_all('a')
			match_date_prev = match_date
			match_date = match.find('td').text
			if match_date == '':
				match_date = match_date_prev
			results = []
			for el in match_info:
				text = (el.text.strip())
				if '(' in el.text.strip():
					results.append(text[0:text.index('(')-1])
					continue
				if text == '':
					continue
				results.append(text)
			results.append(match_round)
			results.append(match_date)

			yield results




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teams.db'
db = SQLAlchemy(app)
scheduler = APScheduler()


class Teams(db.Model):
	id = db.Column(db.Integer,primary_key = True)
	team_name = db.Column(db.String(10))
	rating = db.Column(db.Integer)

	def __repr__(self):
		return f"<teams{self.id}>"


class Matches(db.Model):
	id = db.Column(db.Integer,primary_key = True)
	date = db.Column(db.DateTime)
	team_a = db.Column(db.String(20))
	team_b = db.Column(db.String(20))
	score = db.Column(db.String(5))
	def __repr__(self):
		return f"{team_a} {score} {team_b}"








@app.route('/')
def index():
	teams = Teams.query.order_by(Teams.rating.desc()).limit(20)
	return render_template('index.html',teams = teams)

def scheduled_check():
	global season
	cur_season = str(season)+'-'+str(season+1)
	print(season)
	for match in match_parser(cur_season):
			team_a = match[0]
			team_b = match[1]
			score = match[2]
			match_round = match[3]
			match_date = parser.parse(match[4])
			match_exist = db.session.query(Matches).filter_by(team_a = team_a,team_b = team_b).first() is not None
			if not match_exist:
				M = Matches(date = match_date,team_a = team_a,team_b = team_b,score = score)
				db.session.add(M)
				db.session.commit()
				continue
			if score != db.session.query(Matches).filter_by(team_a = team_a,team_b = team_b).first().score:
				if score == '-:-' or score == 'resch.':
					continue
				# Updates score if match played
				print("score has changed")
				db.session.query(Matches).filter_by(team_a = team_a,team_b = team_b).first().score = score
				db.session.commit()

				# Updates ratings of the teams if score changed
				team_a_rank = int(db.session.query(Teams).filter_by(team_name = team_a).first().rating)
				team_b_rank = int(db.session.query(Teams).filter_by(team_name = team_b).first().rating)
				team_a_score = int(score[:score.index(':')])
				team_b_score = int(score[score.index(':')+1:])

				P = elo_change(team_a,team_b,team_a_rank,team_b_rank,match_round,team_a_score,team_b_score)
				db.session.query(Teams).filter_by(team_name = team_a).first().rating = int(team_a_rank + P)
				db.session.query(Teams).filter_by(team_name = team_b).first().rating = int(team_b_rank - P)
				db.session.commit()
			
			if Matches.query.filter(or_(Matches.score == 'resch.',Matches.score == '-:-')).count() == 0: # IF number of matches ends then iterate to the next season
				season += 1
			

if __name__ == '__main__':
	scheduler.add_job(id = "parse", func = scheduled_check,trigger = 'interval',seconds = 60,max_instances = 1,end_date='2021-12-14 22:15:00',misfire_grace_time=None)
	scheduler.start()
	app.run(host='0.0.0.0',port = 5000,debug = True)
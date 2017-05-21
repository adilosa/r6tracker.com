from flask import Flask, jsonify, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View

import boto3
from boto3.dynamodb.conditions import Key
import requests


app = Flask(__name__)

app.config['DEBUG'] = True
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

Bootstrap(app)
nav = Nav(app)


nav.register_element('frontend_top', Navbar(View('r6tracker', '.overview')))


profileIds = { 
	"ChaosNox": "86fb0498-0b1b-4d21-b621-310cab9bec15",
	"UnfairRainbow": "bcf0ef91-9084-47d9-860d-91a2fdbac260",
	"KrakenMonkey": "ec3061f9-968f-4443-b760-0c3dc354c9c2",
	"whitew0lf2112": "42bff726-304e-44dd-809f-7d0f312a9300"
}


def rank(profileId):
	return boto3.resource('dynamodb').Table("seigestats-players").query(
		Limit=1, KeyConditionExpression=Key('profileId').eq(str(profileId)), ScanIndexForward=False
	)['Items'][0]['stats']

def stats(profileId):
	return boto3.resource('dynamodb').Table("siegestats-stats").query(
		Limit=1, KeyConditionExpression=Key('profileId').eq(str(profileId)), ScanIndexForward=False
	)['Items'][0]['stats']


@app.route("/")
def overview():
	return render_template(
		"index.html", profiles=[
			{ "name": name, "profileId": pid, "rank": rank(pid) } for name, pid in profileIds.items()
		]
	)

@app.route("/profiles/<profileId>")
def profile(profileId):
	return render_template(
		"profile.html", rank=rank(profileId), stats=stats(profileId)
	)


if __name__ == "__main__":
	app.run(host="0.0.0.0", debug=True)

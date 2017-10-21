from flask import Flask, jsonify, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask.ext.cache import Cache

import boto3
from boto3.dynamodb.conditions import Key
import requests


application = Flask(__name__, instance_relative_config=True)

application.config.from_object('config')
application.config.from_pyfile('flask.cfg', silent=True)
application.jinja_env.auto_reload = True
application.config['TEMPLATES_AUTO_RELOAD'] = True

Bootstrap(application)
nav = Nav(application)
cache = Cache(application, config={'CACHE_TYPE': 'simple'})

nav.register_element('frontend_top', Navbar(View('r6tracker', '.overview')))


profileNames = {
    "86fb0498-0b1b-4d21-b621-310cab9bec15": "ChaosNox",
    "bcf0ef91-9084-47d9-860d-91a2fdbac260": "UnfairRainbow",
    "ec3061f9-968f-4443-b760-0c3dc354c9c2": "KrakenMonkey",
    "42bff726-304e-44dd-809f-7d0f312a9300": "whitew0lf2112"
}


@cache.memoize(60)
def rank(profileId, limit=1):
    return [
        item['stats'] for item in boto3.resource('dynamodb', region_name='us-west-2').Table("seigestats-players").query(
            Limit=limit, KeyConditionExpression=Key('profileId').eq(str(profileId)), ScanIndexForward=False
        )['Items'] if item['stats']['update_time'] > '1971'
    ]


@cache.memoize(60)
def stats(profileId, limit=1):
    return [
        augmented_stat(item['stats']) for item in boto3.resource('dynamodb', region_name='us-west-2').Table("siegestats-stats").query(
            Limit=limit, KeyConditionExpression=Key('profileId').eq(str(profileId)), ScanIndexForward=False
        )['Items']
    ]


def augmented_stat(stat):
    stat['operatorpvp_roundplayed:infinite'] = sum([val for key, val in stat.items() if "operatorpvp_roundplayed:" in key])
    return stat


@application.route("/")
def overview():
    return render_template(
        "index.html", profiles=[
            { "name": name, "profileId": pid, "rank": rank(pid)[0] } for pid, name in profileNames.items()
        ]
    )


@application.route("/profiles/<profileId>")
def profile(profileId):
    return render_template(
        "profile.html", ranks=rank(profileId, limit=100), stats=stats(profileId, limit=100), name=profileNames[profileId]
    )


if __name__ == "__main__":
    application.run()


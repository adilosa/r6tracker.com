from flask import Flask, jsonify, render_template
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask.ext.cache import Cache

import boto3
from boto3.dynamodb.conditions import Key
import requests
import gzip, json
from collections import OrderedDict
from io import BytesIO


application = Flask(__name__, instance_relative_config=True)

application.config.from_object('config')
application.config.from_pyfile('flask.cfg', silent=True)
application.jinja_env.auto_reload = True
application.config['TEMPLATES_AUTO_RELOAD'] = True

Bootstrap(application)
nav = Nav(application)
cache = Cache(application, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/tmp/'})

nav.register_element('frontend_top', Navbar(View('r6tracker', '.overview')))


profileNames = OrderedDict([
    ("86fb0498-0b1b-4d21-b621-310cab9bec15", "ChaosNox"),
    ("ec3061f9-968f-4443-b760-0c3dc354c9c2", "KrakenMonkey"),
    ("bcf0ef91-9084-47d9-860d-91a2fdbac260", "UnfairRainbow"),
    ("42bff726-304e-44dd-809f-7d0f312a9300", "whitew0lf2112"),
    ("69d1cb01-ad43-4ff7-b31c-6332ba88b9a8", "HitRegkt"),
    ("71c42f4d-96b6-4fb2-a980-39b92529d116", "SyNySt3r.-")
])

s3 = boto3.resource('s3')


@cache.memoize()
def _cached_datafile(key, etag):
    return BytesIO(s3.Object('r6tracker', key).get()['Body'].read())


@cache.memoize(60)
def _datafile(key):
    return sorted(
        [
            json.loads(line.decode('utf-8'))
            for line in gzip.GzipFile(fileobj=_cached_datafile(key, s3.Object('r6tracker', key).e_tag))
            if line.decode('utf-8').strip()
        ],
        key=lambda i: i['update_time'],
        reverse=True
    )

@cache.memoize(60)
def rank(profileId):
    return [item['stats'] for item in _datafile('profiles/{}/player.jsonl.gz'.format(profileId))]


@cache.memoize(60)
def stats(profileId):
    return [
        with_field(
            augmented_stat(item['stats']), 'update_time', item['update_time']
        ) for item in _datafile('profiles/{}/stats.jsonl.gz'.format(profileId))
    ]


def augmented_stat(stat):
    stat['operatorpvp_roundplayed:infinite'] = sum([val for key, val in stat.items() if "operatorpvp_roundplayed:" in key])
    return stat

def with_field(item, name, value):
    item[name] = value
    return item

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
        "profile.html", ranks=rank(profileId), stats=stats(profileId), name=profileNames[profileId]
    )


if __name__ == "__main__":
    application.run()


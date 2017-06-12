import os
import time
import cPickle
import datetime
import logging
import werkzeug
import optparse
import tornado.wsgi
import tornado.httpserver
import numpy as np
import pandas as pd
from PIL import Image
import cStringIO as StringIO
import urllib
import exifutil
import numpy as np
import flask
from flask import Flask, session, redirect, request, url_for, render_template, jsonify, abort
from flask.ext.login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from oauth import OAuthSignIn
import requests
import json
import re
import urllib2
from flask_googlemaps import Map, GoogleMaps
from flask.ext.cqlalchemy import CQLAlchemy
import os
import PIL
import simplejson
import traceback

from flask import flash, send_from_directory
from flask.ext.bootstrap import Bootstrap
from werkzeug import secure_filename

from flask.ext.login import AnonymousUserMixin
from lib.upload_file import uploadfile
import uuid
import datetime
from cassandra.cqlengine.usertype import UserType
from cassandra.cqlengine import ValidationError

REPO_DIRNAME = os.path.abspath(os.path.dirname(
    os.path.abspath(__file__)) + '/../..')
UPLOAD_FOLDER = '/tmp/webapp_uploads'
LOCAL_FOLDER = '/home/haloi/webwork/web_demo/static'

# Obtain the flask app object
app = flask.Flask(__name__, static_url_path="", static_folder="static")
app.config['CASSANDRA_HOSTS'] = ['127.0.0.1']
app.config['CASSANDRA_KEYSPACE'] = "nehome"
app.config['SECRET_KEY'] = 'hakajsjdhgngjgbmgngdse'
app.config['UPLOAD_FOLDER'] = '/home/haloi/webwork/web_demo/data/'
app.config['THUMBNAIL_FOLDER'] = '/home/haloi/webwork/web_demo/data/thumbnail/'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '94699637185444478',
        'secret': '410wla1aeb68b290cc0b9a3dff952e47a662a4'
    },
    'twitter': {
        'id': '3RzWQclolxWZssIMq5LJqzRZPTl',
        'secret': 'm9TEd58DSEaaatRsrZHpz2EjrVr9fAhsBRxKMo8m3kuIZj3zLwzwIimt'
    }
}

GoogleMaps(app)
bootstrap = Bootstrap(app)
db = CQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'
lm.session_protection = "strong"


class Anonymous(AnonymousUserMixin):

    def __init__(self):
        self.username = 'Guest'
lm.anonymous_user = Anonymous

from web_demo import models

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
from flask import Flask, g, session, redirect, request, url_for, render_template, jsonify, abort
from flask.ext.login import LoginManager, UserMixin, login_user, login_required, logout_user,current_user
from oauth import OAuthSignIn
import requests, json, re, urllib2
from flask_googlemaps import Map, GoogleMaps
from flask.ext.cqlalchemy import CQLAlchemy
import os
import PIL
import simplejson
import traceback
from flask import flash, send_from_directory
from flask.ext.bootstrap import Bootstrap
from werkzeug import secure_filename

from lib.upload_file import uploadfile
import uuid
import datetime
from cassandra.cqlengine.usertype import UserType
from cassandra.cqlengine import ValidationError

from models import Users, Roomads, Propertyrent, Temporoom
from web_demo import app, db, lm

ALLOWED_EXTENSIONS = set(['txt', 'gif', 'png', 'jpg', 'jpeg', 'bmp', 'rar', 'zip', '7zip', 'doc', 'docx'])
IGNORED_FILES = set(['.gitignore'])

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gen_file_name(filename):
    """
    If file was exist already, rename it and return a new name
    """

    i = 1
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        name, extension = os.path.splitext(filename)
        filename = '%s_%s%s' % (name, str(i), extension)
        i = i + 1

    return filename

def create_thumbnai(directory, image):
    try:
        basewidth = 80
        img = Image.open(os.path.join(directory, image))
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)
        img.save(os.path.join(app.config['THUMBNAIL_FOLDER'], image))

        return True

    except:
        print traceback.format_exc()
        return False

# Starting of function calls
def mapAddress(address):
    address_mod = re.sub("[^a-zA-Z0-9 \n\.]", "", address).replace(" ", "+")
    rest_call = "https://maps.googleapis.com/maps/api/geocode/json?address="+address_mod
    location_data = requests.get(rest_call, verify=False).json()
    return location_data

def getLatLng():
    my_ip = urllib2.urlopen("http://ip.42.pl/raw").read().decode("utf-8")
    data_req = requests.get("http://ipinfo.io/"+my_ip, verify=False)
    data_LatLng = json.loads(data_req.text)["loc"]
    lat, lng = data_LatLng.split(",")[0], data_LatLng.split(",")[1]
    return lat, lng

@app.route("/api/<address>", methods=["GET"])
def apiCall(address):
    location_api_data = mapAddress(address)
    if str(location_api_data["status"]) == "OK":
        lat = location_api_data["results"][0]["geometry"]["location"]["lat"]
        lng = location_api_data["results"][0]["geometry"]["location"]["lng"]
        fmt_add = location_api_data["results"][0]["formatted_address"]
        return jsonify({"latitude": lat, "longitude": lng, "Full-Address": fmt_add})
    else:
        abort(404)

@app.route("/locate", methods=["GET", "POST"])
def locate():
    address = str(request.form["address"])
    location_data = mapAddress(address)
    if str(location_data["status"]) == "OK":
        lat = location_data["results"][0]["geometry"]["location"]["lat"]
        lng = location_data["results"][0]["geometry"]["location"]["lng"]
        fmt_add = location_data["results"][0]["formatted_address"]
        location_address = Map(identifier="locationAdd", lat=lat, lng=lng, zoom="15", style="height:400px;width:1000px;margin:0;", markers=[(lat,lng)])
        return render_template("locationAdd.html", location_address=location_address, lat=lat, lng=lng, fmt_add=fmt_add)
    else:
        return render_template("locationError.html")

@app.route("/mhh", methods=["GET", "POST"])
def mapview():

    lat, lng = getLatLng()
    location_accept = Map(identifier="accept", lat=lat, lng=lng, zoom="15", style="height:400px;width:1000px;margin:0;", markers=[(lat,lng)])
    location_decline = Map(identifier="decline", lat=28.4158, lng=-81.2989, zoom="15", style="height:400px;width:1000px;margin:0;", markers=[(28.4158,-81.2989)])
    return render_template("temporoom.html", location_accept=location_accept, location_decline=location_decline, lat=lat, lng=lng)

db.sync_db()
#@app.before_request
@lm.user_loader
def load_user(id):
    q=Users.objects.filter(id=id).allow_filtering()
    #g.user = q
    #print g.user.username
    return q.get()

@app.before_request
def load_users():
    g.user = current_user.username
    #print g.user

@app.route('/')
def index():
    return flask.render_template('searchtempo.html', has_result=False)

@app.route('/data')
@login_required
def userdata():
    #result = Users.get(uid = '5b6962dd-3f90-4c93-8f61-eabfa4a803e2')
    #Users.create(uid=uuid.uuid4(), username='devadeep', firstname='devadeep', lastname='shaym', email='devadeep@gmail.com')
    result = Users.get(email = 'ishantim28@gmail.com')
    return result.username

@app.route('/login')
def login():
    return flask.render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email, firstname, lastname= oauth.callback()
    session['username'] = username
    session['user_id'] = social_id
    print firstname, lastname, email
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = Users.objects.filter(email=email).first()
    print user
    if not user:
        user = Users.create(email=email, username = username, id = social_id, firstname=firstname, lastname=lastname, joined=datetime.datetime.now().date())
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/maps/temporoom/search', methods=['GET', 'POST'])
def gettemporoomsearch():
    address='jurong'
    location_data = mapAddress(address)
    if str(location_data["status"]) == "OK":
        lat = location_data["results"][0]["geometry"]["location"]["lat"]
        lng = location_data["results"][0]["geometry"]["location"]["lng"]
        fmt_add = location_data["results"][0]["formatted_address"]
        location_address = Map(identifier="locationAdd", lat=lat, lng=lng, zoom="15", style="height:400px;width:700px;margin:0;", markers=[(lat,lng)])
        location_accept = Map(identifier="accept", lat=lat, lng=lng, zoom="15", style="height:400px;width:700px;margin:0;", markers=[(lat,lng)])
        return render_template("temporoom.html", location_accept=location_accept, lat=lat, lng=lng)

@app.route('/maps/temporoom', methods=['GET', 'POST'])
def gettemporoom():

    address = str(request.form["address"])
    location_data = mapAddress(address)
    if str(location_data["status"]) == "OK":
        lat = location_data["results"][0]["geometry"]["location"]["lat"]
        lng = location_data["results"][0]["geometry"]["location"]["lng"]
        fmt_add = location_data["results"][0]["formatted_address"]
        print location_data
        print location_data["results"]
        location_address = Map(identifier="locationAdd", lat=lat, lng=lng, zoom="15", style="height:400px;width:700px;margin:0;", markers=[(lat,lng)])
        location_accept = Map(identifier="accept", lat=lat, lng=lng, zoom="15", style="height:400px;width:700px;margin:0;", markers=[(lat,lng)])
        return render_template("temporoom.html", location_accept=location_accept, lat=lat, lng=lng)

@app.route('/maps/temporoom/results', methods=['GET', 'POST'])
def getresultstemporoom():
    address = str(request.form["address"])
    result = Temporoom.objects.filter(district=address, zipcode=781009)
    print result[0].zipcode
    print result 
    if not result:
        has_result = False
    no_of_result = len(result)
    idx_result = range(0, no_of_result)
    location_data = mapAddress(address)
    if str(location_data["status"]) == "OK":
        lat = location_data["results"][0]["geometry"]["location"]["lat"]
        lng = location_data["results"][0]["geometry"]["location"]["lng"]
        fmt_add = location_data["results"][0]["formatted_address"]
        #print location_data
        #print location_data["results"]
        location_address = Map(identifier="locationAdd", lat=lat, lng=lng, zoom="11", style="height:400px;width:700px;margin:0;", markers=[(lat,lng)])
    return render_template("temporoom.html", has_result=True, idx=idx_result, result=result, location_accept=location_address, lat=lat, lng=lng)
filenames=[]
@app.route("/upload", methods=['GET', 'POST'])
def upload():
    session['fileimages'] = []
    directory = os.path.join(app.config['UPLOAD_FOLDER'], g.user)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print directory
        print 'directry created'
    if request.method == 'POST':
        file = request.files['file']
        #pprint (vars(objectvalue))
        if file:
            filename = secure_filename(file.filename)
            filenames.append(filename)
            session['fileimages'].append(filename)
            filename = gen_file_name(filename)
            mimetype = file.content_type

            if not allowed_file(file.filename):
                result = uploadfile(name=filename, type=mimetype, size=0, not_allowed_msg="Filetype not allowed")

            else:
                # save file to disk
                #uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file_path = os.path.join(directory, filename)
                file.save(uploaded_file_path)

                # create thumbnail after saving
                if mimetype.startswith('image'):
                    create_thumbnai(directory, filename)

                # get file size after saving
                size = os.path.getsize(uploaded_file_path)

                # return json for js call back
                result = uploadfile(name=filename, type=mimetype, size=size)
            session['images'] = [result.get_file()]
            return simplejson.dumps({"files": [result.get_file()]})

    if request.method == 'GET':
        # get all file in ./data directory
        files = [ f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory,f)) and f not in IGNORED_FILES ]

        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(directory, f))
            file_saved = uploadfile(name=f, size=size)
            file_display.append(file_saved.get_file())

        return simplejson.dumps({"files": file_display})

    return redirect(url_for('index'))

@app.route("/delete/<string:filename>", methods=['DELETE'])
def delete(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], g.user, filename)
    file_thumb_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            if os.path.exists(file_thumb_path):
                os.remove(file_thumb_path)

            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})

# serve static files
@app.route("/thumbnail/<string:filename>", methods=['GET'])
def get_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename=filename)

@app.route("/data/<string:filename>", methods=['GET'])
def get_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), g.user, filename=filename)
@app.route('/listproperty', methods=['GET', 'POST'])
def listproperty():
    return render_template('listproperty.html')

@app.route('/searchtempo', methods=['GET', 'POST'])
def searchtempo():
    return render_template('imageuploader.html')

@app.route('/listrent', methods=['GET', 'POST'])
def listrent():
    return render_template('listrent.html')

@app.route('/roomneed', methods=['GET', 'POST'])
def roomneed():
    return render_template('roomneed.html')

@app.route('/handleform/roomneed', methods=['GET', 'POST'])
def processroomneed():
    full_address = request.form.get('full_address')
    country = request.form.get('country')
    state = request.form.get('state')
    street = request.form.get('street')
    locality = request.form.get('locality')
    aptunit = request.form.get('aptunit')
    zipcode = request.form.get('zipcode')
    district = request.form.get('district')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    distancefromwork = request.form.get('distancefromwork')
    aboutme = request.form.getlist('aboutme')
    profession = request.form.get('profession')
    numbed = request.form.get('nobed')
    furnishtype = request.form.get('furnishtype')
    numtenant = request.form.get('noguest')
    numbath = request.form.get('nobath')
    amenities = request.form.getlist('amenities')
    pricemonth = request.form.get('pricemonth')
    availability = request.form.get('availability')
    if availability:
        dateformat = availability.split('/')
        formatdate = dateformat[2]+"-"+dateformat[0]+"-"+dateformat[1]
    else:
        formatdate = datetime.datetime.now().date()
    leaseterm = request.form.get('leaseterm')
    preference = request.form.getlist('rentrules')
    description = request.form.get('description')
    minlease = leaseterm.split('-')[0]
    socialid = '2676cb3782cc3g3'
    Roomads.create(district=district,pricemonth=pricemonth,propid=uuid.uuid4(), posteddate=datetime.datetime.now().date(),
            posted=datetime.datetime.now(),minlease=minlease,
            zipcode=zipcode,socialid=socialid,fulladdress=full_address,country=country,
            state=state, street=street, locality=locality,
            distancefromwork=distancefromwork, aboutme=aboutme,
            profession=profession, numbed=numbed, furnishtype=furnishtype,
            numtenant=numtenant, numbath=numbath, amenities=amenities,
            availability=formatdate,
            preference=preference, lat=lat, lng=lng, description=description)
    print country
    print state
    print street
    print aptunit
    print amenities
    print preference
    print availability
    return leaseterm
@app.route('/handleform/listproperty', methods=['GET', 'POST'])
def processlistform():
    country = request.form.get('country')
    state = request.form.get('state')
    street = request.form.get('street')
    aptunit = request.form.get('aptunit')
    amenities = request.form.getlist('specialfeatures')
    print country
    print state
    print street
    print aptunit
    print amenities
    return country
@app.route('/handleform/rent', methods=['GET', 'POST'])
def processrentform():
    full_address = request.form.get('full_address')
    country = request.form.get('country')
    state = request.form.get('state')
    street = request.form.get('street')
    locality = request.form.get('locality')
    aptunit = request.form.get('aptunit')
    zipcode = request.form.get('zipcode')
    district = request.form.get('district')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    pricemonth = request.form.get('pricemonth')
    numbed = request.form.get('nobed')
    numbath = request.form.get('nobath')
    rtype = request.form.get('placetype')
    ptype = request.form.get('proptype')
    furnishtype = request.form.get('furnishtype')
    numtenant = request.form.get('noguest')
    placedescription = request.form.get('placedescription')
    amenities = request.form.getlist('amenities')
    outdooramenities = request.form.getlist('guestspace')
    specialfeatures = request.form.getlist('specialfeatures')
    availability = request.form.get('availability')
    if availability:
        dateformat = availability.split('/')
        formatdate = dateformat[2]+"-"+dateformat[0]+"-"+dateformat[1]
    else:
        formatdate = datetime.datetime.now().date()
    possesion = request.form.get('possesion')
    leaseterm = request.form.get('leaseterm')
    preference = request.form.getlist('guestprefer')
    rentrules = request.form.getlist('rentrules')
    description = request.form.get('description')
    minlease = leaseterm.split('-')
    maxlease = minlease[1].split(' ')[1]
    socialid = '2676cb3782cc3g3'
    print minlease
    print numbath, numbed, numtenant
    print rtype
    Propertyrent.create(district=district,rent=pricemonth,propid=uuid.uuid4(),posteddate=datetime.datetime.now().date(),posted=datetime.datetime.now(),
            zipcode=zipcode, socialid=socialid, rtype=rtype, fulladdress=full_address,country=country,
            state=state, street=street, locality=locality,lease=[int(minlease[0]), int(maxlease)],
            possesion=possesion, numbed=numbed, furnishtype=furnishtype,
            numtenant=numtenant, numbath=numbath, amenities=amenities,
            availability=formatdate,
            preference=preference, lat=lat, lng=lng, placedescription=placedescription,outdooramenities=outdooramenities, specialamenities=specialfeatures, rentrules=rentrules)
    print country
    print state
    print street
    print aptunit
    print amenities
    print preference
    print availability
    return leaseterm
@app.route('/handleform/temporoom', methods=['GET', 'POST'])
def processtemporoomform():
    full_address = request.form.get('full_address')
    country = request.form.get('country')
    state = request.form.get('state')
    street = request.form.get('street')
    locality = request.form.get('locality')
    aptunit = request.form.get('aptunit')
    zipcode = request.form.get('zipcode')
    district = request.form.get('district')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    numbed = request.form.get('nobed')
    numbath = request.form.get('nobath')
    rtype = request.form.get('placetype')
    ptype = request.form.get('proptype')
    furnishtype = request.form.get('furnishtype')
    numguest = request.form.get('noguest')
    placedescription = request.form.get('placedescription')
    amenities = request.form.getlist('amenities')
    outdooramenities = request.form.getlist('guestspace')
    specialamenities = request.form.getlist('samenities')
    preference = request.form.getlist('guestprefer')
    houserules = request.form.getlist('houserules')
    dates = request.form.getlist('dates')
    possesion = request.form.get('possesion')
    leaseterm = request.form.get('leaseterm')
    description = request.form.get('description')
    minstay = request.form.get('minday')
    maxstay = request.form.get('maxday')
    advancenotice = request.form.get('advancenotice')
    guestfrequency = request.form.get('guestfrequency')
    preptime = request.form.get('preptime')
    bookingwindow = request.form.get('bookingwindow')
    pricerange = request.form.get('pricerange')
    baseprice = request.form.get('baseprice')
    currency = request.form.get('currency')
    hostfrequency = request.form.get('hostfrequency')
    securitydeposit = request.form.get('securitydeposit')
    cleaningfee = request.form.get('cleaningfee')
    weekdiscount = request.form.get('weekdiscount')
    monthdiscount = request.form.get('monthdiscount')
    cancellation = request.form.get('cancellation')
    howguestbook = request.form.get('howguestbook')
    socialid = '2w76cb3782cc3g3'
    print rtype, district, baseprice, minstay, zipcode, socialid
    Temporoom.create(district=district, propid=uuid.uuid4(),posteddate=datetime.datetime.now().date(), posted=datetime.datetime.now(),
            zipcode=zipcode, socialid=socialid, minstay=minstay, maxstay=maxstay, rtype=rtype, fulladdress=full_address,country=country,
            state=state, street=street, locality=locality,howguestbook=howguestbook,
            numbed=numbed, furnishtype=furnishtype,securitydeposit=securitydeposit,
            accomodates=numguest, numbath=numbath, amenities=amenities,hostfrequency=hostfrequency, guestfrequency=guestfrequency,
            unavailabledates=dates,weeklydiscount=weekdiscount, monthlydiscount=monthdiscount,cancellation=cancellation, baseprice=baseprice, pricerange=[0,1], currency=currency, cleaningfee=cleaningfee,advancenotice=advancenotice, preptime=preptime, bookingwindow=bookingwindow,
            preference=preference, lat=lat, lng=lng, placedescription=placedescription,outdooramenities=outdooramenities, specialamenities=specialamenities, houserules=houserules)
    print country
    print state
    print street
    print aptunit
    print amenities
    print preference
    return country
@app.route('/handleform/image', methods=['GET', 'POST'])
def processimage():
    try:
        files = flask.request.files.getlist('file')
        filenames=[]
        filenames_images = []
        for ffile in files:
                imgfile = werkzeug.secure_filename(ffile.filename)
                filename_ = str(datetime.datetime.now()).replace(' ', '_') + imgfile
                filename = os.path.join(UPLOAD_FOLDER, filename_)
                ffile.save(filename)
                filenames.append(filename)
                filenames_images.append(filename_)
                print 'Upload Success!'
                logging.info('Saving to %s.', filename)
    except Exception as err:
        logging.info('Uploaded image open error: %s', err)
        return flask.render_template(
                'index.html', has_result=True,
                result=(False, 'Cannot open uploaded image.')
                )
    imagefiles=[]
    all_result = []
    number_of_image = len(filenames)
    index_data = range(0, number_of_image)
    time_taken = 0
    noImage = len(filenames)
    return str(noImage)

def start_tornado(app, port=5000):
    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(app))
    http_server.listen(port)
    print("Tornado server starting on port {}".format(port))
    tornado.ioloop.IOLoop.instance().start()

def start_from_terminal(app):
        app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    start_from_terminal(app)

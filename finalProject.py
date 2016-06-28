from flask import Flask, render_template, url_for, request, redirect, jsonify, flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu App"

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    # print "Access token is:"
    # print access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = credentials.access_token
    # print "Access token is:"
    # print login_session['access_token']

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print "Access token is:"
    print access_token
    # access_token = credentials.access_token
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/restaurants/')
def showRestaurants():
    # restaurants = session.query(Restaurant).all()
    restaurants = session.query(Restaurant).order_by(Restaurant.name.asc()).all()
    return render_template('restaurants.html', restaurants = restaurants)

@app.route('/restaurants/new', methods=['GET','POST'])
def newRestaurant():
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['newRest'])
        session.add(newRestaurant)
        flash("New Restaurant Created")
        session.commit()
        return redirect(url_for('showRestaurants'))
    return render_template('newRestaurants.html')

@app.route('/restaurants/<int:restaurant_id>/edit', methods=['GET','POST'])
def editRestaurant(restaurant_id):
    if request.method == 'POST':
        restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
        restaurant.name = request.form['editRest']
        flash("Restaurant Successfully Edited")
        session.commit()
        return redirect(url_for('showRestaurants'))
    name = session.query(Restaurant.name).filter(Restaurant.id == restaurant_id).one()
    return render_template('editRestaurants.html', restaurant_id = restaurant_id, name = name)

@app.route('/restaurants/<int:restaurant_id>/delete', methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
    if request.method == 'POST':
        try:
            restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).one()
            session.delete(restaurant)
            flash("Restaurant Successfully Deleted")
            session.commit()
            return redirect(url_for('showRestaurants'))
        except:
            return redirect(url_for('showRestaurants'))
    name = session.query(Restaurant.name).filter(Restaurant.id == restaurant_id).one()
    print name
    return render_template('deleteRestaurants.html', restaurant_id = restaurant_id, name = name)

@app.route('/restaurants/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    name = session.query(Restaurant.name).filter(Restaurant.id == restaurant_id).one()
    menu = session.query(MenuItem).join(MenuItem.restaurant).filter(Restaurant.id==restaurant_id).order_by(MenuItem.course)
    return render_template('menu.html', restaurant_id = restaurant_id, menu = menu, name = name)

@app.route('/restaurants/<int:restaurant_id>/menu/new', methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if request.method == 'POST':
        newMenu = MenuItem(name = request.form['newItem'], restaurant_id = restaurant_id, description = request.form['newDescription'], price=request.form['newPrice'], course = request.form['course'])
        # newMenu = MenuItem(name = request.form['newItem'], restaurant_id = restaurant_id)
        session.add(newMenu)
        flash("New Menu Item Created")
        session.commit()
        return redirect(url_for('showMenu',restaurant_id=restaurant_id))
    name = session.query(Restaurant.name).filter(Restaurant.id == restaurant_id).one()
    return render_template('newMenuItem.html', restaurant_id = restaurant_id, name = name)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    if request.method == 'POST':
        menuItem = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id,MenuItem.id == menu_id).one()
        menuItem.name = request.form['editMenu']
        menuItem.description = request.form['editDescription'] 
        menuItem.price = request.form['editPrice'] 
        menuItem.course = request.form['editCourse']
        flash("Menu Item Successfully Edited")
        session.commit()
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    jam = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id,MenuItem.id == menu_id).one()
    print jam.name
    return render_template('editMenuItem.html', restaurant_id = restaurant_id, menu_id = menu_id, jam = jam)

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if request.method == 'POST':
        try:
            menuItem = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id,MenuItem.id == menu_id).one()
            session.delete(menuItem)
            flash("Menu Item Successfully Deleted")
            session.commit()
            return redirect(url_for('showMenu', restaurant_id = restaurant_id))
        except:
            return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    jam = session.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id,MenuItem.id == menu_id).one()
    return render_template('deleteMenuItem.html', restaurant_id = restaurant_id, jam = jam)

@app.route('/restaurants/JSON')
def showRestaurantsJSON():
    restaurants = session.query(MenuItem).all()
    return jsonify(restaurants=[r.serialize for r in restaurants])

@app.route('/restaurants/<int:restaurant_id>/menu/JSON')
def showRestaurantMenuJSON(restaurant_id):
    menu = session.query(MenuItem).filter(MenuItem.restaurant_id==restaurant_id).all()
    return jsonify(menu=[m.serialize for m in menu])

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menu_itemz = session.query(MenuItem).filter(MenuItem.id==menu_id).one()
    return jsonify(Menu_Item=menu_itemz.serialize)


if __name__ == '__main__':
    app.secret_key = 'xvmZcviLG0U8z77LxgKHmgAO'
    app.debug = True
    app.run(host = '0.0.0.0', port=5000)
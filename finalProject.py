from flask import Flask, render_template, url_for, request, redirect, jsonify, flash
# import jsonify
app = Flask(__name__)
app.secret_key = 'super_secret_key'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


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
        return redirect(url_for('showRestaurants'))
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
    app.debug = True
    app.run(host = '0.0.0.0', port=5000 )
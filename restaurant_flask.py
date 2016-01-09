from flask import Flask
app = Flask(__name__)

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
def restaurants():
    restaurants = session.query(Restaurant).all()
    output = ""
    for rest in restaurants:
    	output += rest.name
    	output += "</br>"
    return output

@app.route('/restaurants/<int:restaurant_id>/')
def

@app.route('/restaurants/new')

@app.route('/restaurants/<int:restaurant_id>/menu/new')

@app.route('/restaurants/<int:restaurant_id>/edit')

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit')

@app.route('/restaurants/<int:restaurant_id>/delete')

@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete')


if __name__ == '__main__':
	app.debug = True
	app.run(host = '0.0.0.0', port=5000 )
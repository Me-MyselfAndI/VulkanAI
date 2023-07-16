from flask import Blueprint, render_template, request, jsonify, redirect, url_for

views = Blueprint(__name__, "views")

@views.route("/")
def home():
    return render_template("index.html")

@views.route("/profile/<username>")
def profile(username):
    return render_template("profile.html", name=username)

#Query
@views.route("/users")
def users():
    args = request.args
    name = args.get('name')
    return render_template("home.html", name=name)

#Json
@views.route("/json")
def get_json():
    return jsonify({'name' : 'nick', 'intellect': 10})

#Get json data if its sent there
@views.route("/data")
def get_data():
    data = request.json#If json data is sent to specific route
    return jsonify(data)

#Redirect to different page
@views.route("/go-to")
def go_to():
    return redirect(url_for("views.get_json"))#Write name of function to which page you wanna go to



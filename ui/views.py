from flask import Blueprint, render_template, request, jsonify, redirect, url_for, render_template_string
from web_search.search_engine import SearchEngine


views = Blueprint(__name__, "views")

@views.route("/")
def home():
    return render_template("index.html")

@views.route("/search-result")
def search_result():
    # Create the engine
    search_engine = SearchEngine()
    # Use update-links method to refresh the search results (stored inside the class).
    # Start entry is 0 by default, it's the pagination offset
    search_engine.update_links("Chupa-chups", start_entry=0)
    # Open link (default opens 0th link, otherwise use link_number argument)
    page = search_engine.get_first_website()
    # Write css into file to connect it to html
    css_code = page['css']
    with open('static/result.css', 'w') as css_file:
        for i in range(len(css_code)):
            css_file.write(css_code[i])
    return render_template_string(page['html'])

@views.route("/go-to")
def go_to():
    return redirect(url_for("views.search_result"))



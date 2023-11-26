from flask import Blueprint, render_template, request, jsonify, redirect, url_for, render_template_string
from web_search.search_engine import SearchEngine
from compression.ai.gpt_engine import GPTEngine
#from compression.compression_engine import CompressionEngine
import yaml, os, flask, json
from compression.main import ScrapingController

#Init Classes

views = Blueprint(__name__, "views")

#Get Chat GPT API
with open(r'keys\keys.yaml') as keys_file:
    keys = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']

    gpt_engine = GPTEngine(keys['gpt-api']['api-url'], keys['gpt-api']['org-url'])

scraping_controller = ScrapingController(gpt_engine)
search_engine = SearchEngine()

@views.route("/", methods=["POST", "GET", "PUT"])
def home():
    return render_template("index.html")
#10121E
@views.route("/search-result", methods=["POST", "GET", "PUT"])
def search_result():
    formattedSearch = ""
    # I want to buy used honda sedan with 130k or less miles, under 6k in good condition 30 miles away from atlanta
    if request.method == "POST":
        received_data = request.get_json()
        print(f"received data: {received_data['data']}")
        formattedSearch = gpt_engine.get_response("Reformat this text into a searchable query: " + str(received_data["data"]))
        print(formattedSearch)

        #get_parsed_website_html()

        # Use update-links method to refresh the search results (stored inside the class).
        # Start entry is 0 by default, it's the pagination offset
        search_engine.update_links(formattedSearch.strip("\""), start_entry=0)
        # Open link (default opens 0th link, otherwise use link_number argument)
        page = search_engine.get_first_website()
        #Get page url
        website_url = page["url"]
        print(website_url)
        website = {
             'url': website_url,
             'html': page["html"]
        }

        #Save HTML
        with open("ui/templates/result.html", "w", encoding="utf-8") as file:
            file.write(scraping_controller.get_parsed_website_html(website, formattedSearch))
            print("Saved")
        """
        #Save CSS
        css_code = page['css']
        with open('ui/static/result.css', 'w') as css_file:
            for i in range(len(css_code)):
                css_file.write(css_code[i])
            print("Saved CSS")
        #Send success message so we can start transfering user to new page
        """
        #Finish receiving data
        message = received_data['data']
        return_data = {
            "status": "success",
            "message": f"received: {message}"
        }
        flask.Response(response=json.dumps(return_data), status=201)

    return render_template("result.html")
    """# Write css into file to connect it to html
    #Insert link to css into html text that will be rendered to connect them
    css_link = '<link href="../static/result.css" rel="stylesheet">\n'
    tag = '</head>'
    if tag in page['html']:
        add_pos = len(tag)
        position = page['html'].index(tag) + add_pos
        new_html = page['html'][:position] + css_link + page['html'][position:]
    try:
        return render_template_string(new_html)
    except:
        return render_template_string(page['html'])"""

#TESTING FUNCTIONS, CAN BE DELETED
@views.route("/test", methods=["POST", "GET", "PUT"])
def test():
    # Use update-links method to refresh the search results (stored inside the class).
    # Start entry is 0 by default, it's the pagination offset
    search_engine.update_links("Chupa-chups",start_entry=0)
    # Open link (default opens 0th link, otherwise use link_number argument)
    page = search_engine.get_first_website()
    return render_template_string(page['html'])

@views.route("/go-to")
def go_to():
    return redirect(url_for("views.search_result"))

@views.route("/format-search", methods=["GET", "POST"])
def format_search():
    if request.method == "POST":
        received_data = request.get_json()
        print(f"received data: {received_data['data']}")
        formattedSearch = gpt_engine.get_response("Reformat this text into a searchable query: " + str(received_data["data"]))
        print(formattedSearch)
    return render_template("index.html")



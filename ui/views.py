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
#Clean results file
result_file = open("ui/templates/result.html", 'w')

#MAIN FUNCTIONS
@views.route("/", methods=["POST", "GET", "PUT"])
def home():
    return render_template("index.html")

@views.route("/search-result", methods=["POST", "GET", "PUT"])
def search_result():
    formattedSearch = ""
    result_file = open("ui/templates/result.html", 'r')#Open results file to Check if it has anything loaded in

    # I want to buy used honda sedan with 130k or less miles, under 6k in good condition 30 miles away from atlanta
    if request.method == "POST":
        received_data = request.get_json()
        print(f"received data: {received_data['data']}")
        print(f"Prefered Website: {received_data['pref-website']}")
        formattedSearch = gpt_engine.get_response("Reformat this text into a searchable query: " + str(received_data["data"]))
        print(formattedSearch)

        # Use update-links method to refresh the search results (stored inside the class).
        # Start entry is 0 by default, it's the pagination offset
        search_engine.update_links(formattedSearch.strip("\""), start_entry=0)
        # Open link (default opens 0th link, otherwise use link_number argument)
        page = search_engine.get_first_website()
        #Get page url
        website_url = page["url"]
        #If user has a prefered website to search on, use that website
        if received_data['pref-website'] == "":
            print("No prefered website")
        else:
            website_url = received_data['pref-website']
        print(website_url)
        website = {
             'url': website_url,
             'html': page["html"]
        }
        print(scraping_controller.get_parsed_website_html(website, formattedSearch))
        #Save HTML ---------------------------------------------------------------
        with open("ui/templates/result.html", "w", encoding="utf-8") as file:
            file.write(scraping_controller.get_parsed_website_html(website, formattedSearch))
            print("Saved")

        #Add Overlay button which allows users to go back on page
        #Might not be neccessary right now cause we putting all of the results in template
        cssLink = '\n<link href="../static/templatestyle.css" rel="stylesheet">'
        scriptLink = "<script src='../static/redirect.js'></script>\n"
        headTag = '<head>'
        bodyTag = '<body>'
        endBodyTag = '</body>'
        backButton = '<div id="overlay-button"><button onclick="redirectToSearch()" class="button-style" role="button">Back to Search</button></div>\n'
        content = open("ui/templates/result.html", "r", encoding="utf-8").read()#Get current content of the html file to change it

        with open("ui/templates/result.html", "w", encoding="utf-8") as result_file:
            #Add link to button css file
            if headTag in content:
                addPos = len(headTag)
                pos = content.index(headTag) + addPos
                content = content[:pos] + cssLink + content[pos:]
            # Add button itself
            if bodyTag in content:
                addPos = len(bodyTag)
                pos = content.index(bodyTag) + addPos
                content = content[:pos] + backButton + content[pos:]
            # Add script to redirect user back to search
            if endBodyTag in content:
                pos = content.index(endBodyTag)
                content = content[:pos] + scriptLink + content[pos:]
            result_file.write(content)

        #Transfer template to final result file and start transfering important data into the template
        template = ""
        """with open("ui/templates/template.html", "r", encoding="utf-8") as template_file:
            template = template_file.read()
        with open("ui/templates/final_result.html", "w", encoding="utf-8") as result_file:
            result_file.write(template)
            print(content)
            for line in (line.strip("\n") for line in content):
               if "h2" in line:
                   print(line)"""


        #Send success message so we can start reloade page to render new html
        message = received_data['data']
        return_data = {
            "status": "success",
            "message": f"received: {message}"
        }
        flask.Response(response=json.dumps(return_data), status=201)

        result_file = open("ui/templates/result.html", 'r')

    if result_file.read() == "":
        return render_template("loader.html")
    else:
        return render_template("result.html")
    #Extra Code
    """css_link = '<link href="../static/result.css" rel="stylesheet">\n'
    tag = '</head>'
    if tag in page['html']:
        add_pos = len(tag)
        position = page['html'].index(tag) + add_pos
        new_html = page['html'][:position] + css_link + page['html'][position:]
    try:
        return render_template_string(new_html)
    except:
        return render_template_string(page['html'])"""
    """
    #Save CSS
    css_code = page['css']
    with open('ui/static/result.css', 'w') as css_file:
        for i in range(len(css_code)):
            css_file.write(css_code[i])
        print("Saved CSS")
    """

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



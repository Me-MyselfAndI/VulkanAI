import sys

#sys.path.append(r"/var/www/html/")  # Server Side
from flask import Blueprint, render_template, request, redirect, url_for, render_template_string, jsonify, Response
from web_search.search_engine import SearchEngine
from compression.ai.gpt_engine import GPTEngine
import yaml, os, flask, json, requests, time
from compression.main import ScrapingController

# Init Classes
views = Blueprint(__name__, "views")

# Get Chat GPT API
#with open(r'/var/www/html/keys/keys.yaml') as keys_file:  # Server Side
with open(r'keys/keys.yaml') as keys_file: #Local Side
    keys = yaml.load(keys_file, yaml.FullLoader)['keys']['compression']['ai']

    gpt_engine = GPTEngine(keys['gpt-api']['api-url'], keys['gpt-api']['org-url'])

scraping_controller = ScrapingController(llm='gpt', cheap_llm='gemini')
search_engine = SearchEngine()
searching_type = "basic"
#content = open("/var/www/html/ui/templates/template.html", "r", encoding="utf-8").read()  # Server Side
content = open("ui/templates/template.html", "r",encoding="utf-8").read() #Local Side
finalContent = ""


# MAIN FUNCTIONS
@views.route("/", methods=["POST", "GET", "PUT"])
def home():
    # css_file = open("ui/static/result.css", 'w')  # Clean css file
    return render_template("index.html")


@views.route("/go-to")
def go_to():
    print("Redirected to search result")
    return redirect(url_for("views.search_result"))


@views.route("/final-result", methods=["POST", "GET", "PUT"])
def final_result():
    global finalContent

    if request.method == "POST":
        try:
            print("Loading selected page")
            received_data = request.get_json()
            formatted_search = gpt_engine.get_response(
                "Reformat this text into a searchable query: " + str(received_data["data"]))
            url = received_data["pref-website"]
            print(url)
            page = search_engine.get_website(url=url)
            parse_website(received_data, formatted_search, page, finalContent)
        except Exception as e:
            print("Failed to load, exception ", e)

    print("Showing actual result")
    print("final result test")

    #Fixes Jinja exception with unclosed comment lines
    splitContent = ""
    splitContent = iter(finalContent.splitlines())
    fixedContent = ""
    for line in splitContent:
        count_open = line.count('{#')
        count_close = line.count('#}')
        if count_open > count_close:
            diff = count_open - count_close
            line += '#}' * diff
        fixedContent += line + " "
    print("Fixed Content")
    print(fixedContent)
    print("Final Content")
    print(finalContent)



    return render_template_string(fixedContent)


@views.route("/search-result", methods=["POST", "GET", "PUT"])
def search_result():
    global content
    # I want to buy used honda sedan with 130k or less miles, under 6k in good condition 30 miles away from atlanta
    formatted_search = ""
    if request.method == "GET":
        print("Get request received")
        print("Request Headers ", request.headers)  # Keep For Debug
        print("Request Environ ", request.environ)
    if request.method == "POST":
        print("Post Request Received")

        received_data = request.get_json()  # received_data = request.json
        print(received_data)
        print(f"received data: {received_data['data']}")
        print(f"Prefered Website: {received_data['pref-website']}")
        print(f"Search Method:  {received_data['search-type']}")
        searching_type = received_data['search-type']
        formatted_search = gpt_engine.get_response(
            "Reformat this text into a searchable query: " + str(received_data["data"]))
        print(f"Formatted Search: {formatted_search}")

        # # Use update-links method to refresh the search results (stored inside the class).
        # Start entry is 0 by default, it's the pagination offset
        search_engine.update_links(formatted_search.strip("\""), start_entry=0)

        # Get all of the related links and show them to the user
        links_list = search_engine.get_urls_by_indices()
        print(links_list)

        if searching_type == "basic":
            print("Basic Search")
            # Save links in HTML ---------------------------------------------------------------
            #content = open("/var/www/html/ui/templates/template.html", "r", encoding="utf-8").read()  # Server Side
            content = open("ui/templates/template.html", "r", encoding="utf-8").read() #Local Side
            list = "<ul>"
            mainDiv = "<div id='maincontent'>"
            # Save HTML to variable
            if mainDiv in content:
                addPos = len(mainDiv)
                pos = content.index(mainDiv) + addPos
                content = content[:pos] + "<h2 id='search-input-title'>" + formatted_search + "</h2>" + content[pos:]
            if list in content:
                for link in links_list:
                    addPos = len(list)
                    pos = content.index(list) + addPos
                    content = content[
                              :pos] + f"<li><img src='{link['icon']}'><a href='{link['url']}' class='result-link'>" + \
                              link['title'] + "</a><br><p>" + link['url'] + "</p></li>" + content[pos:]

            print("Redirected to go-to page")
            return redirect(url_for("views.go_to"))

        elif searching_type == "speed":
            print("Speed Search")
            # Open link (default opens 0th link, otherwise use link_number argument)
            page = search_engine.get_first_website()

            parse_website(received_data, formatted_search, page, content)

            print("Redirected to go-to page")
            return redirect(url_for("views.go_to"))

    print("Showing actual result")
    return render_template_string(content)


# HELPER FUNCTIONS
# Parse selected website and show user relevant information
def parse_website(received_data: dict, formatted_search: str, page: dict, render_var):
    global content, finalContent
    # Get page url
    website_url = page['url']
    # If user has a prefered website to search on, use that website
    if received_data['pref-website'] == "":
        print("No prefered website")
    else:
        website_url = received_data['pref-website']
    print(website_url)
    website = {
        'url': website_url,
        'html': page["html"]
    }

    # Save CSS
    """try:
        css_code = page['css']
        print("Saved CSS")
        print(css_code)
    except:
        print("Failed to get css code")"""

    # Save HTML ---------------------------------------------------------------
    returnedResponse = scraping_controller.get_parsed_website_html(website, formatted_search)
    if returnedResponse["status"] == "ok":
        render_var = str(returnedResponse["response"])
        #print(render_var)
        print("Saved HTML")
    else:
        print(f"\u001b[31m Error encountered: {returnedResponse['response']}\u001b[0m")

    # Add Overlay
    # finalContent = add_overlay(render_var)
    finalContent = render_var

    # Send success message so we can start reload page to render new html
    return_data = {
        "status": "success",
        "message": f"received",
        "content": finalContent
    }
    #endpoint_url = "https://vulkanai.org:5000/views/final-result"  # Server Side
    endpoint_url = "http://127.0.0.1:8000/views/final-result" #Local Side
    response = requests.post(endpoint_url, json=return_data)
    if response.status_code == 200 or response.status_code == 201:
        print("Sent data")
    else:
        print("Failed to send")


# Add VulkanAI overlay with back button and slider
def add_overlay(resultHTML: str):
    # Add Overlay button which allows users to go back on page
    cssLink = '\n<link href="ui/static/templatestyle.css" rel="stylesheet">\n<link href="../static/result.css" rel="stylesheet">'
    scriptLink = "<script src='../ui/static/redirect.js'></script>\n"
    headTag = '<head>'
    bodyTag = '<body>'
    endBodyTag = '</body>'
    backButton = '<div id="overlay-button"><button onclick="redirectToSearch()" class="button-style" role="button">Back to Search</button></div>\n'
    slider = '<div id="slider-container"><input type="range" min="-100" max="0" value="0" class="range blue" id="slider"/><p class="num" id="start">0</p><p class="num" id="one">1</p><p class="num" id="mid">2</p><p class="num" id="three">3</p><p class="num" id="end">4</p></div>'

    # Add link to button css file
    if headTag in resultHTML:
        addPos = len(headTag)
        pos = resultHTML.index(headTag) + addPos
        resultHTML = resultHTML[:pos] + cssLink + resultHTML[pos:]
    # Add slider
    if bodyTag in resultHTML:
        addPos = len(bodyTag)
        pos = resultHTML.index(bodyTag) + addPos
        resultHTML = resultHTML[:pos] + slider + resultHTML[pos:]
    # Add button itself
    if bodyTag in resultHTML:
        addPos = len(bodyTag)
        pos = resultHTML.index(bodyTag) + addPos
        resultHTML = resultHTML[:pos] + backButton + resultHTML[pos:]
    # Add script to redirect user back to search
    if endBodyTag in resultHTML:
        pos = resultHTML.index(endBodyTag)
        resultHTML = resultHTML[:pos] + scriptLink + resultHTML[pos:]

    print("Added overlay")
    print(resultHTML)
    return resultHTML




#TESTING FUNCTIONS, CAN BE DELETED
"""
@views.route("/test", methods=["POST", "GET", "PUT"])
def test():
    # Use update-links method to refresh the search results (stored inside the class).
    # Start entry is 0 by default, it's the pagination offset
    search_engine.update_links("Chupa-chups",start_entry=0)
    # Open link (default opens 0th link, otherwise use link_number argument)
    page = search_engine.get_first_website()
    return render_template_string(page['html'])

@views.route("/format-search", methods=["GET", "POST"])
def format_search():
    if request.method == "POST":
        received_data = request.get_json()
        print(f"received data: {received_data['data']}")
        formatted_search = gpt_engine.get_response("Reformat this text into a searchable query: " + str(received_data["data"]))
        print(formatted_search)
    return render_template("index.html")


#Extra Code
    css_link = '<link href="../static/result.css" rel="stylesheet">\n'
    tag = '</head>'
    if tag in page['html']:
        add_pos = len(tag)
        position = page['html'].index(tag) + add_pos
        new_html = page['html'][:position] + css_link + page['html'][position:]
    try:
        return render_template_string(new_html)
    except:
        return render_template_string(page['html'])

# Transfer template to final result file and start transfering important data into the template
template = ""
with open("ui/templates/template.html", "r", encoding="utf-8") as template_file:
    template = template_file.read()
with open("ui/templates/final_result.html", "w", encoding="utf-8") as result_file:
    result_file.write(template)
    print(content)
    for line in (line.strip("\n") for line in content):
       if "h2" in line:
           print(line)

#with open('/var/www/html/ui/static/result.css', 'w') as css_file:#Server Side
    #with open('ui/static/result.css', 'w') as css_file: #Local Side
        #for i in range(len(css_code)):
            #try:
                #css_file.write(css_code[i])
            #except:
                #print("Error while writting a line")
                
                """
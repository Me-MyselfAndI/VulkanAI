#from sqlite3 import Cache

from flask import Flask
from views import views
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(views, url_prefix="/views")
CORS(app, resources={r"/*": {"origins": "http://192.168.1.97"}})
#cache = Cache(app, config={'CACHE_TYPE': 'simple'})

if __name__ == '__main__':
    app.run(debug=True, port=8000) # Local Side
    #app.run(debug=True, port=5000) # Server Side


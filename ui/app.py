from flask import Flask, session
from views import views
from flask_cors import CORS
from flask_caching import Cache
import ssl
from __init__ import cache

#Cache Config
config = {
    "CACHE_TYPE": "simple", #Was SimpleCache
    "CACHE_THRESHOLD": 300
}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(views, url_prefix="/views")
app.config.from_mapping(config)
cache.init_app(app)#To avoid circular imports, init cache in __init__ file
app.secret_key = b''

CORS(app, resources={r"/views/*": {"origins": "https://vulkanai.org"}})

# Load the SSL certificate and key
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#context.load_cert_chain(certfile='../ssl/fullchain.pem', keyfile='../ssl/privkey.pem') #Server Side

if __name__ == '__main__':
    # Run the app with HTTPS enabled
    #app.run(debug=True, port=5000, host='0.0.0.0', ssl_context=context) #Server Side
    app.run(debug=True, port=8000) # Local Side



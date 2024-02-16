from flask import Flask
from views import views
from flask_cors import CORS
import ssl

app = Flask(__name__, template_folder="templates", static_folder="static")
app.register_blueprint(views, url_prefix="/views")

CORS(app, resources={r"/views/*": {"origins": "https://vulkanai.org"}})

# Load the SSL certificate and key
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#context.load_cert_chain(certfile='../ssl/fullchain.pem', keyfile='../ssl/privkey.pem') #Server Side

if __name__ == '__main__':
    # Run the app with HTTPS enabled
    #app.run(debug=True, port=5000, host='0.0.0.0', ssl_context=context) #Server Side
    app.run(debug=True, port=8000) # Local Side



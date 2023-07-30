from flask import Flask, render_template, redirect, session
import requests
import webbrowser
from spotipy.oauth2 import SpotifyOAuth
import json, os

app = Flask(__name__)

# OAuth
app.secret_key = "super secret key"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'
secrets = json.load(open("client_secret.json", "r"))


#for spotify 
BASE_URL = 'https://api.spotify.com/v1/'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
redirect_uri = "http://127.0.0.1:5000/redirect/"
scope = ["user-read-private", "user-read-email", 'playlist-modify-public', 
                'playlist-modify-private', 'playlist-read-private', 'user-library-modify', 
                'user-library-read', 'user-top-read']
clientID=secrets["client_id"]
clientSecret=secrets["client_secret"]
googleMapsKey=secrets["google_maps"]
TOKEN_INFO='token_info'


# Default page
@app.route("/")
def defaultPage():
    ##fart = getTripDuration("Boston, MA", "Salem, MA", "Driving")
    ##print(fart)
    return render_template("home.html")


#Log in
@app.route("/login")
def SpotifyLogin():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

#Logs out from Spotify
def SpotifyLogout():
    session.clear()
    if os.path.exists(".cache"):
        os.remove(".cache")
    webbrowser.open_new("https://accounts.spotify.com/en/logout")
    return render_template('home.html', message="You have been logged out.")


#Creates spotify oauth object
def create_spotify_oauth():
    return SpotifyOAuth(
            clientID,
            clientSecret,
        redirect_uri="http://127.0.0.1:5000/redirect/",
         scope=["user-read-private", "user-read-email", 'playlist-modify-public', 
                'playlist-modify-private', 'playlist-read-private', 'user-library-modify', 
                'user-library-read', 'user-top-read'])


def getTripDuration(orgin, destination, transportation):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=" + orgin +"&destinations=" + destination +"&mode=" + transportation + "&key=" + googleMapsKey
    payload={}
    headers = {}
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code >= 200 and response.status_code < 300:
            results = response.json
            return results["rows"]["elements"]["distance"]["text"]
    except:
        return "invalid location"
    
def getPlaylist(duration):
    return "need to implement"


if __name__ == "__main__":
    app.run(debug=True)
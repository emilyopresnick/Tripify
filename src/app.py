from flask import Flask, request, render_template, jsonify,url_for,redirect, session, url_for
import webbrowser, spotipy, math
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import json, os

app = Flask(__name__)


# OAuth
app.secret_key = "super secret key"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'
secrets = json.load(open("client_secret.json", "r"))
if os.path.exists(".cache"):
  os.remove(".cache")

#for spotify 
BASE_URL = 'https://api.spotify.com/v1/'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
redirect_uri = "http://127.0.0.1:5000/redirect/"
scope = ["user-read-private", "user-read-email", 'playlist-modify-public', 
                'playlist-modify-private', 'playlist-read-private', 'user-library-modify', 
                'user-library-read', 'user-top-read']
client_id=secrets["client_id"]
client_secret=secrets["client_secret"]
TOKEN_INFO='token_info'


#Log in
@app.route("/login")
def SpotifyLogin():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

#logs out user from application by logging out of spotify
@app.route("/logout")
def SpotifyLogout():
    session.clear()
    if os.path.exists(".cache"):
        os.remove(".cache")
    webbrowser.open_new("https://accounts.spotify.com/en/logout")
    return render_template('home.html', message="You have been logged out.")


#creates spotify oauth object
def create_spotify_oauth():
    return SpotifyOAuth(
            client_id=secrets["client_id"],
            client_secret=secrets["client_secret"],
        redirect_uri="http://127.0.0.1:5000/redirect/",
         scope=["user-read-private", "user-read-email", 'playlist-modify-public', 
                'playlist-modify-private', 'playlist-read-private', 'user-library-modify', 
                'user-library-read', 'user-top-read'])




if __name__ == "__main__":
    app.run(port=5000, debug=True)
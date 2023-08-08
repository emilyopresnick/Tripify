from flask import Flask, render_template, redirect, session, request, url_for
import webbrowser, time, requests, json, os, random
from spotipy.oauth2 import SpotifyOAuth

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
   ## fart = getTripDuration("Boston, MA", "Salem, MA", "Driving")
   ## print(fart)
   #print(getSavedSongs)
   return render_template("login.html")


@app.route("/home")
def homePage():
    return render_template("home.html")


@app.route("/redirect/")
def redirectPage():
    #gets the access code from oauth to exchange for the access token
    sp_oauth=create_spotify_oauth()
    session.clear()
    code=request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO]=token_info
    token_info = getAccessToken()
    headers=session['headers']
    session['genres'] = getGenres(headers)
    getSavedSongs(headers)
   
    return redirect(url_for('homePage', _external=True))


#Log in to spotify
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

#gets the access token from spotify oauth and refreshes if expired
def getAccessToken():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
         raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
         sp_oauth = create_spotify_oauth()
         token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    #store headers in session variable for api requests
    headers = {'Authorization': 'Bearer {token}'.format(token=token_info['access_token'])}
    session['headers']=headers
    return token_info 


def getTripDuration(orgin, destination, transportation):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=" + orgin +"&destinations=" + destination +"&mode=" + transportation + "&key=" + googleMapsKey
    payload={}
    headers = {}
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        results = response.json()
        return results["rows"][0]["elements"][0]["duration"]["text"]
    except:
        return "invalid location"
    
def getPlaylist(duration, orgin, destination):
    headers=session["headers"]

    #get user name
    r=requests.get(BASE_URL + "me", headers=headers)
    r=r.json()
    userName = r['display_name']
    
    #make empty spotify playlist
    r = f"https://api.spotify.com/v1/users/{userName}/playlists"
    request_body = json.dumps({
           "name": "Tripify: "+ orgin + " to " + destination,
         })
    response = requests.post(url = r, data = request_body, headers=headers)
    playlist_id = response.json()['id']


    #get users saved tracks
    savedSongs=[]
    r=requests.get(BASE_URL + "me/tracks?limit=50", headers=headers)
    r=r.json()
    for track in r["items"]["track"]: 
        savedSongs.append(track["id"])
    return "need to implement"


def getSavedSongs(headers):
    savedSongs={}
    url = BASE_URL + "me/tracks?limit=50"
    hasNext = True
    while (hasNext):
        r=requests.get(url, headers=headers)
        r=r.json()
        for track in r['items']:
                id = track['track']['id']
                
                newReq = requests.get(BASE_URL + "audio-features?ids=" + id, headers = headers)
                req = newReq.json()
                durationMS = req['audio_features'][0]['duration_ms']

                name = track['track']['name']
                artist = track['track']['artists'][0]['name']
                duration =  durationMS / 1000
                

                savedSongs[name] = (artist, duration)

        if (r['next'] is None):
           hasNext = False
        else:
             url=r["next"]

    return savedSongs
        

def getGenres(headers):
    genres=[]
    url = BASE_URL + "me/top/artists"
    hasNext = True
    
    while (hasNext):
        r=requests.get(url, headers=headers)
        r=r.json()
        for artists in r['items']:
            genres.append((artists['genres']))

        if "next" in url:
            url=r["next"]
        else:
            hasNext = False

    flatlist=[element for sublist in genres for element in sublist]
    genreList = [*set(flatlist)]
    return genreList

def getRecs(headers):
    recSongs = []
    genres = getGenres(headers)
    randomGenres = (random.choices(genres, k=3))
    r=requests.get(BASE_URL + "recommendations/?seed_genres=" + randomGenres + "&limit=50", headers=headers)
    r=r.json()
    for album in r['tracks']:
        track_info = {
                        'name': album['track']['name'],
                        'artist': album['track']['artist'],
                        'duration': album['duration_ms'] / 1000
                    }

        recSongs.append(track_info)
    return getRecs

def getDuration(track):
    return track['duration']

def sortByDuration(list):
    #TODO
    return 0



if __name__ == "__main__":
    app.run(debug=True)
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

    topSongs = getTopTracks(headers, "medium")
    print(len(topSongs))
    savedSongs = getSavedSongs(headers, 0, 50)
    print(len(savedSongs))
    recSongs = getRecs(headers)
    print(len(recSongs))
    allSongs = topSongs | savedSongs | recSongs
    print(len(allSongs))
    print(allSongs)
    
   
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


    return "need to implement"

#get certain amount of users saved songs, if we want all of the saved songs then set amt = 10,000
def getSavedSongs(headers, offset, amt):
    limit = 50
    if(amt < limit):
        limit = amt
    savedSongs={}
    url = BASE_URL + "me/tracks?limit=" + str(limit) + "&offset=" + str(offset)
    while (amt > 0):
        r=requests.get(url, headers=headers)
        r=r.json()

        #if offset is greater than amount of liked songs, items will be blank so return empty dictionary
        if (r['items'] == []):
            break

        for track in r['items']:
                
                id = track['track']['id']
                
                
                name = track['track']['name']
                artist = track['track']['artists'][0]['name']
                duration = track['track']['duration_ms'] /1000
                
                savedSongs[id] = (name, artist, duration)

        #If there are no more liked songs
        if (r['next'] is None):
           amt = 0

        #Because the API call is for limit of 50, after each call decrease amt by 50
        #update the URL to get the next songs
        else:
            amt -= 50
            url=r["next"]

    return savedSongs
        

def getRecs(headers):
    recSongs = {}

    r = requests.get(BASE_URL + "recommendations/available-genre-seeds", headers=headers)
    r=r.json()
    availGenre = []

    for genres in r['genres']:
        availGenre.append(genres)
    randomGenres = (random.choices(availGenre, k=3))
    randomGenres = ','.join(randomGenres)
    
    r=requests.get(BASE_URL + "recommendations/?seed_genres=" + randomGenres + "&limit=50", headers=headers)
    r=r.json()
    for album in r['tracks']:
        id = album['id']
        name = album['name']
        artist =  album['artists'][0]['name']
        duration = album['duration_ms']

        recSongs[id] = (name, artist, duration)

    return recSongs

def getTopTracks(headers, timeRange):
    if (timeRange == "short"):
        ADD_ON ="me/top/tracks?limit=50&time_range=short_term"
    elif (timeRange == "long"):
        ADD_ON = "me/top/tracks?limit=50&time_range=long_term"
    else:
        ADD_ON = "me/top/tracks?limit=50"

    tracks={}
    url = BASE_URL + ADD_ON
    hasNext = True
    while (hasNext):
        r=requests.get(url, headers=headers)
        r=r.json()
        for track in r['items']:
                id = track['id']
                name = track['name']
                artist = track['artists'][0]['name']
                duration =  track['duration_ms'] / 1000
                
                tracks[id] = (name, artist, duration)

        if (r['next'] is None):
           hasNext = False
        else:
             url=r["next"]

    return tracks


def getDuration(track):
    return track['duration']

#sort by shortest to longest
def sortByDuration(trackDict):
    #TODO
    return 0



if __name__ == "__main__":
    app.run(debug=True)
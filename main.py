import requests
import urllib.parse
import json

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template

app = Flask(__name__)
app.secret_key = 'prod'

CLIENT_ID = '80e827ecab6b4e7e917903695b58da4a'
CLIENT_SECRET = '2445808a930348b69adf5a8cfc421196'
REDIRECT_URL = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize' 
TOKEN_URL = 'https://accounts.spotify.com/api/token' 
API_BASE_URL = 'https://api.spotify.com/v1/' 

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read user-read-recently-played'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URL, 
        'show_dialog': True #should change to true later for login
    }
   
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
           'code': request.args['code'],
           'grant_type': 'authorization_code',
           'redirect_uri': REDIRECT_URL, 
           'client_id': CLIENT_ID,
           'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)

        token_info = response.json()
        session['access_token'] = token_info['access_token'] 
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/pages')

@app.route('/pages')
def view_pages():
    return render_template('redirect.html')

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = json.loads(response.content)["items"] 

    return render_template('playlist.html', data=playlists)

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grand_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')

@app.route('/user-fav')
def user_fav():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    
    url = f"{API_BASE_URL}me/top/tracks?time_range=short_term" 
      
    response = requests.get(url, headers=headers)
    favourite = json.loads(response.content)["items"]
    
    #fav = json.loads(response.content)

    return render_template('fav.html', data=favourite)
    #return fav

@app.route('/recently-played')
def recent():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }

    url = f"{API_BASE_URL}me/player/recently-played"

    response = requests.get(url, headers=headers)
    recent = json.loads(response.content)["items"]

    return render_template('recent.html', data=recent)
    # return recent
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
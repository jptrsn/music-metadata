from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import requests
from metadata import find_incorrect_tracks, mark_track_as_fixed  # Import the function from your metadata script
import time

app = Flask(__name__)
DATABASE = 'owntone.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Custom filter to use zip in Jinja2 templates
@app.template_filter('zip')
def zip_filter(*args):
    return zip(*args)

# Home route to display matches and allow filtering by artist and album
@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get list of unique artists and albums that have matches in the track_links table
    cursor.execute('''
        SELECT DISTINCT it.Artist
        FROM itunes_tracks it
        JOIN track_links tl ON it.track_id = tl.itunes_track_id
        ORDER BY it.Artist
    ''')
    artists = cursor.fetchall()

    cursor.execute('''
        SELECT DISTINCT ot.album
        FROM tracks ot
        JOIN track_links tl ON ot.id = tl.owntone_track_id
        ORDER BY ot.album
    ''')
    albums = cursor.fetchall()
    
    # Default query to fetch all matched tracks
    query = '''
        SELECT it.Name AS itunes_track_name, it.Artist AS itunes_artist, it.Album AS itunes_album, it.Rating as itunes_rating,
               ot.title AS owntone_track_name, ot.artist AS owntone_artist, ot.album AS owntone_album, ot.rating as owntone_rating
        FROM track_links tl
        JOIN itunes_tracks it ON it.track_id = tl.itunes_track_id
        JOIN tracks ot ON ot.id = tl.owntone_track_id
    '''
    
    filters = []
    params = []
    
    # Check if the user applied filters
    selected_artist = request.form.get('artist')
    selected_album = request.form.get('album')
    
    if selected_artist:
        filters.append('it.Artist = ?')
        params.append(selected_artist)
    
    if selected_album:
        filters.append('ot.album = ?')
        params.append(selected_album)
    
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    
    # Fetch the matched records based on the filters
    cursor.execute(query, params)
    matches = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html', matches=matches, artists=artists, albums=albums, selected_artist=selected_artist, selected_album=selected_album)

@app.route('/incorrect-tracks', methods=['GET', 'POST', 'PATCH'])
def incorrect_tracks():
    if request.method == 'POST':
        # Update track information
        track_id = request.form['track_id']
        updated_artist = request.form['updated_artist']
        updated_album = request.form['updated_album']
        updated_title = request.form['updated_title']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tracks
            SET artist = ?, album = ?, title = ?
            WHERE id = ?
        ''', (updated_artist, updated_album, updated_title, track_id))

        conn.commit()
        conn.close()

        # Mark the track as fixed
        mark_track_as_fixed(track_id)
        
        return redirect(url_for('incorrect_tracks'))

    # Fetch incorrect tracks
    incorrect_tracks = find_incorrect_tracks()
    
    return render_template('incorrect_tracks.html', incorrect_tracks=incorrect_tracks)

@app.route('/mark-fixed', methods=['POST'])
def mark_track_fixed():
    track_id = request.form['track_id']
    
    # Mark the track as fixed
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fixed_tracks (track_id) VALUES (?)
    ''', (track_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('incorrect_tracks'))

@app.route('/mark-album-fixed', methods=['POST'])
def mark_album_fixed():
    track_id = request.form['track_id']
    
    # Mark the track as fixed
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO fixed_tracks (track_id)
        SELECT id
        FROM tracks
        WHERE album_id = (
            SELECT album_id
            FROM tracks
            WHERE id = ?
        ) AND id NOT IN (SELECT track_id FROM fixed_tracks)
    ''', (track_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('incorrect_tracks'))

# Function to sort the array by artist_sort and title_sort
def sort_tracks_by_artist_and_title(tracks):
    return sorted(tracks, key=lambda x: (x['artist_sort'].lower(), x['album_sort'].lower(), x['title_sort']))

@app.route('/unrated', methods=['GET', 'POST'])
def unrated():
    if request.method == 'POST':
        # Iterate through the submitted form data
        conn = get_db_connection()
        cursor = conn.cursor()

        track_updates = []

        for key, value in request.form.items():
            # Check if the key corresponds to a track rating
            if key.startswith('updated_rating_'):
                track_id = int(key.split('_')[2])  # Extract the track ID from the key
                updated_rating = int(value) if value.isdigit() else 0  # Get the selected rating

                # Only update if the rating is greater than zero
                if int(updated_rating) > 0:
                    cursor.execute('''
                        UPDATE tracks
                        SET rating = ?
                        WHERE id = ?
                    ''', (updated_rating, track_id))

                    # Prepare the update for the API request
                    track_updates.append({
                        "id": track_id,
                        "rating": updated_rating
                    })

                    # Mark the track as fixed
                    cursor.execute('''
                        INSERT OR IGNORE INTO fixed_tracks (track_id)
                        VALUES (?)
                    ''', (track_id,))

        conn.commit()

        # Make a PUT request to update all ratings via the API
        if track_updates:
            api_url = "http://192.168.1.13:3689/api/library/tracks"
            payload = {"tracks": track_updates}
            
            # Send the PUT request
            try:
                response = requests.put(api_url, json=payload)
                response.raise_for_status()  # Raise an error for bad responses
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")

            time.sleep(1)

        conn.close()
        
        return redirect(url_for('unrated'))

    # GET request handling
    # GET request handling
    unrated = []
    response = requests.get("http://192.168.1.13:3689/api/search?type=tracks&expression=rating=0&media_kind=music")
    
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        unrated = data.get("tracks", {}).get("items", [])  # Get items from the response
        unrated = sort_tracks_by_artist_and_title(unrated)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.id, t.title, t.artist, t.album
            FROM tracks t
            WHERE t.rating = 0
            ORDER BY t.artist, t.album
        ''')
        unrated = cursor.fetchall()
        conn.close()

    return render_template('unrated.html', unrated=unrated)

# Function to search tracks by song name and artist
def search_tracks(song_name, artist_name):
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.title, t.artist, t.album
        FROM tracks t
        WHERE t.title LIKE ? AND t.artist LIKE ?
    ''', (f'%{song_name}%', f'%{artist_name}%'))
    results = cursor.fetchall()
    conn.close()
    return results

@app.route('/unmatched_tracks', methods=['GET', 'POST'])
def unmatched_tracks():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()

    # Query to find unmatched tracks and join them with the tracks table
    cursor.execute('''
        SELECT it.track_id, it.Name, it.Artist, it.Album,
            GROUP_CONCAT(t.id) AS owntone_track_ids,
            GROUP_CONCAT(t.title) AS titles,
            GROUP_CONCAT(t.artist) AS artists,
            GROUP_CONCAT(t.album) AS albums
        FROM itunes_tracks it
        LEFT JOIN tracks t ON LOWER(it.Name) = LOWER(t.title) AND LOWER(it.Artist) = LOWER(t.artist)
        WHERE it.track_id NOT IN (SELECT itunes_track_id FROM track_links)
        AND t.id NOT IN (SELECT owntone_track_id FROM track_links)
        GROUP BY it.track_id
    ''')

    # Fetch all rows from the query result and convert to a list of dictionaries
    unmatched_tracks = []
    for row in cursor.fetchall():
        unmatched_tracks.append({
            'track_id': row[0],
            'title': row[1],
            'artist': row[2],
            'album': row[3],
            'matches': []  # Prepare to store the matches in the expected structure
        })
        
        # Add the matches directly as a list of dictionaries
        if row[4] and row[5] and row[6] and row[7]:  # Ensure titles and artists are not None
            owntone_track_ids = row[4].split(',')
            titles = row[5].split(',')
            artists = row[6].split(',')
            albums = row[7].split(',')
            for id, title, artist, album in zip(owntone_track_ids, titles, artists, albums):
                unmatched_tracks[-1]['matches'].append({
                    'id': id,
                    'title': title,
                    'artist': artist,
                    'album': album
                })

    conn.close()

    # Filter to exclude unmatched tracks with empty matches
    filtered_unmatched_tracks = [track for track in unmatched_tracks if len(track['matches']) > 1]
    
    return render_template('unmatched_tracks.html', unmatched_tracks=filtered_unmatched_tracks)




# Function to link tracks
def link_tracks(itunes_track_ids, owntone_track_ids):
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # If we're linking multiple tracks, zip them together
    if isinstance(itunes_track_ids, list) and isinstance(owntone_track_ids, list):
        for itunes_track_id, owntone_track_id in zip(itunes_track_ids, owntone_track_ids):
            cursor.execute('''
                INSERT INTO track_links (itunes_track_id, owntone_track_id) 
                VALUES (?, ?)
            ''', (itunes_track_id, owntone_track_id))
    else:
        # For a single track
        cursor.execute('''
            INSERT INTO track_links (itunes_track_id, owntone_track_id) 
            VALUES (?, ?)
        ''', (itunes_track_ids, owntone_track_ids))

    conn.commit()
    conn.close()

# Route to handle linking the selected tracks
@app.route('/link_tracks', methods=['POST'])
def link_tracks_route():
    # Retrieve track IDs from the form, allowing for both single and multiple submissions
    itunes_track_ids = request.form.getlist('itunes_track_id[]')
    owntone_track_ids = request.form.getlist('owntone_track_id[]')

    # Call the link_tracks function with either single or multiple IDs
    link_tracks(itunes_track_ids if itunes_track_ids else None,
                owntone_track_ids if owntone_track_ids else None)

    return redirect(url_for('unmatched_tracks'))


@app.route('/play_track', methods=['POST'])
def play_track():
    # Get the track ID from the request JSON
    track_id = request.json.get('track_id')

    # Check if track_id is provided
    if not track_id:
        return jsonify({"error": "Track ID is required"}), 400

    # Base URL for adding a track to the queue
    base_url = "http://192.168.1.13:3689/api/queue/items/add"
    
    # Define the parameters
    params = {
        'uris': f'library:track:{track_id}',  # Use the track_id provided as an argument
        'clear': 'true',                     # Clear the current queue before adding
        'playback': 'start'                  # Start playback immediately
    }

    # Make the PUT request to the OwnTone API
    try:
        # Make the POST request with URL parameters
        response = requests.post(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            return jsonify({"message": "Track is now playing."}), 200
        else:
            return jsonify({"error": "Failed to play track", "details": response.text}), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "An error occurred while connecting to the OwnTone server", "details": str(e)}), 500

@app.route('/itunes_tracks', methods=['GET', 'POST'])
def itunes_tracks():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Initial query
    query = 'SELECT * FROM itunes_tracks WHERE 1=1'
    params = []

    # Filtering based on user input
    if request.method == 'POST':
        artist = request.form.get('artist')
        album = request.form.get('album')
        genre = request.form.get('genre')

        if artist:
            query += ' AND "Artist" LIKE ?'
            params.append(f'%{artist}%')
        if album:
            query += ' AND "Album" LIKE ?'
            params.append(f'%{album}%')
        if genre:
            query += ' AND "Genre" LIKE ?'
            params.append(f'%{genre}%')

    # Execute the query
    cursor.execute(query, params)
    tracks = cursor.fetchall()
    conn.close()

    return render_template('itunes_tracks.html', tracks=tracks)

if __name__ == '__main__':
    app.run(port=8000, debug=True)

import requests
import sqlite3

# Function to create the 'tracks' table in the SQLite database
def create_tracks_table():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Create the 'tracks' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            title_sort TEXT,
            artist TEXT,
            artist_sort TEXT,
            album TEXT,
            album_sort TEXT,
            album_id TEXT,
            album_artist TEXT,
            album_artist_sort TEXT,
            album_artist_id TEXT,
            genre TEXT,
            comment TEXT,
            year INTEGER,
            track_number INTEGER,
            disc_number INTEGER,
            length_ms INTEGER,
            rating INTEGER,
            play_count INTEGER,
            skip_count INTEGER,
            time_added TEXT,
            date_released TEXT,
            seek_ms INTEGER,
            type TEXT,
            samplerate INTEGER,
            bitrate INTEGER,
            channels INTEGER,
            usermark INTEGER,
            media_kind TEXT,
            data_kind TEXT,
            path TEXT,
            uri TEXT,
            artwork_url TEXT,
            FOREIGN KEY(album_id) REFERENCES albums(id),
            FOREIGN KEY(album_artist_id) REFERENCES artists(id)
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to insert track data dynamically into the 'tracks' table
def insert_track(track):
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Track fields to insert into the database
    fields = []
    values = []
    
    # Add each available field to the fields and values lists
    if 'id' in track:
        fields.append('id')
        values.append(track['id'])
    if 'title' in track:
        fields.append('title')
        values.append(track['title'])
    if 'title_sort' in track:
        fields.append('title_sort')
        values.append(track['title_sort'])
    if 'artist' in track:
        fields.append('artist')
        values.append(track['artist'])
    if 'artist_sort' in track:
        fields.append('artist_sort')
        values.append(track['artist_sort'])
    if 'album' in track:
        fields.append('album')
        values.append(track['album'])
    if 'album_sort' in track:
        fields.append('album_sort')
        values.append(track['album_sort'])
    if 'album_id' in track:
        fields.append('album_id')
        values.append(track['album_id'])
    if 'album_artist' in track:
        fields.append('album_artist')
        values.append(track['album_artist'])
    if 'album_artist_sort' in track:
        fields.append('album_artist_sort')
        values.append(track['album_artist_sort'])
    if 'album_artist_id' in track:
        fields.append('album_artist_id')
        values.append(track['album_artist_id'])
    if 'genre' in track:
        fields.append('genre')
        values.append(track['genre'])
    if 'comment' in track:
        fields.append('comment')
        values.append(track['comment'])
    if 'year' in track:
        fields.append('year')
        values.append(track['year'])
    if 'track_number' in track:
        fields.append('track_number')
        values.append(track['track_number'])
    if 'disc_number' in track:
        fields.append('disc_number')
        values.append(track['disc_number'])
    if 'length_ms' in track:
        fields.append('length_ms')
        values.append(track['length_ms'])
    if 'rating' in track:
        fields.append('rating')
        values.append(track['rating'])
    if 'play_count' in track:
        fields.append('play_count')
        values.append(track['play_count'])
    if 'skip_count' in track:
        fields.append('skip_count')
        values.append(track['skip_count'])
    if 'time_added' in track:
        fields.append('time_added')
        values.append(track['time_added'])
    if 'date_released' in track:
        fields.append('date_released')
        values.append(track['date_released'])
    if 'seek_ms' in track:
        fields.append('seek_ms')
        values.append(track['seek_ms'])
    if 'type' in track:
        fields.append('type')
        values.append(track['type'])
    if 'samplerate' in track:
        fields.append('samplerate')
        values.append(track['samplerate'])
    if 'bitrate' in track:
        fields.append('bitrate')
        values.append(track['bitrate'])
    if 'channels' in track:
        fields.append('channels')
        values.append(track['channels'])
    if 'usermark' in track:
        fields.append('usermark')
        values.append(track['usermark'])
    if 'media_kind' in track:
        fields.append('media_kind')
        values.append(track['media_kind'])
    if 'data_kind' in track:
        fields.append('data_kind')
        values.append(track['data_kind'])
    if 'path' in track:
        fields.append('path')
        values.append(track['path'])
    if 'uri' in track:
        fields.append('uri')
        values.append(track['uri'])
    if 'artwork_url' in track:
        fields.append('artwork_url')
        values.append(track['artwork_url'])
    
    # Construct the SQL query dynamically
    query = f"INSERT OR REPLACE INTO tracks ({', '.join(fields)}) VALUES ({', '.join(['?' for _ in values])})"
    
    # Execute the query with the values
    cursor.execute(query, values)
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to fetch tracks for a specific album
def fetch_tracks_for_album(album_id):
    # The URL for fetching tracks for a specific album by its ID
    url = f'http://192.168.1.13:3689/api/library/albums/{album_id}/tracks'
    
    try:
        # Make a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Iterate through the 'items' array
            if 'items' in data:
                for track in data['items']:
                    # Insert each track into the database
                    insert_track(track)
                print(f"Inserted {len(data['items'])} tracks for album {album_id} into the database.")
            else:
                print(f"No 'items' found in the response for album {album_id}")
        else:
            print(f"Failed to fetch tracks for album {album_id}. Status code: {response.status_code}")
    
    except requests.RequestException as e:
        print(f"An error occurred while fetching tracks for album {album_id}: {e}")

# Function to fetch all albums from the database
def fetch_all_albums():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Fetch all albums from the albums table
    cursor.execute('SELECT id FROM albums')
    albums = cursor.fetchall()
    
    conn.close()
    return albums

# Main function to fetch tracks for all albums and insert them into the database
def fetch_and_store_tracks():
    # Fetch all albums from the database
    albums = fetch_all_albums()
    
    # Fetch tracks for each album
    for album in albums:
        album_id = album[0]  # Extract the album ID from the tuple
        fetch_tracks_for_album(album_id)

if __name__ == "__main__":
    # Create the tracks table if it doesn't exist
    create_tracks_table()
    
    # Fetch and store tracks for all albums in the database
    fetch_and_store_tracks()

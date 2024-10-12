import requests
import sqlite3

# Function to create the 'albums' table in the SQLite database
def create_albums_table():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Create the 'albums' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS albums (
            id TEXT PRIMARY KEY,
            name TEXT,
            name_sort TEXT,
            artist TEXT,
            artist_id TEXT,
            track_count INTEGER,
            length_ms INTEGER,
            time_added TEXT,
            in_progress BOOLEAN,
            media_kind TEXT,
            data_kind TEXT,
            date_released TEXT,
            year INTEGER,
            uri TEXT,
            artwork_url TEXT,
            FOREIGN KEY(artist_id) REFERENCES artists(id)
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to insert album data into the 'albums' table
def insert_album(album):
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Insert album data into the albums table
    cursor.execute('''
        INSERT OR REPLACE INTO albums (
            id, name, name_sort, artist, artist_id, track_count, length_ms, time_added, 
            in_progress, media_kind, data_kind, date_released, year, uri, artwork_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        album.get('id'),
        album.get('name'),
        album.get('name_sort'),
        album.get('artist'),
        album.get('artist_id'),
        album.get('track_count'),
        album.get('length_ms'),
        album.get('time_added'),
        album.get('in_progress'),
        album.get('media_kind'),
        album.get('data_kind'),
        album.get('date_released'),
        album.get('year'),
        album.get('uri'),
        album.get('artwork_url')
    ))
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to fetch albums for a specific artist
def fetch_albums_for_artist(artist_id):
    # The URL for fetching albums for a specific artist by their ID
    url = f'http://192.168.1.13:3689/api/library/artists/{artist_id}/albums'
    
    try:
        # Make a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Iterate through the 'items' array
            if 'items' in data:
                for album in data['items']:
                    # Insert each album into the database
                    insert_album(album)
                print(f"Inserted {len(data['items'])} albums for artist {artist_id} into the database.")
            else:
                print(f"No 'items' found in the response for artist {artist_id}")
        else:
            print(f"Failed to fetch albums for artist {artist_id}. Status code: {response.status_code}")
    
    except requests.RequestException as e:
        print(f"An error occurred while fetching albums for artist {artist_id}: {e}")

# Function to fetch all artists from the database
def fetch_all_artists():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Fetch all artists from the artists table
    cursor.execute('SELECT id FROM artists')
    artists = cursor.fetchall()
    
    conn.close()
    return artists

# Main function to fetch albums for all artists and insert them into the database
def fetch_and_store_albums():
    # Fetch all artists from the database
    artists = fetch_all_artists()
    
    # Fetch albums for each artist
    for artist in artists:
        artist_id = artist[0]  # Extract the artist ID from the tuple
        fetch_albums_for_artist(artist_id)

if __name__ == "__main__":
    # Create the albums table if it doesn't exist
    create_albums_table()
    
    # Fetch and store albums for all artists in the database
    fetch_and_store_albums()

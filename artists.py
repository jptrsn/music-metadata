import requests
import sqlite3
import json

# Function to create SQLite database and artists table
def create_database():
    # Create a new SQLite database called 'owntone'
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Create an 'artists' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artists (
            id TEXT PRIMARY KEY,
            name TEXT,
            name_sort TEXT,
            album_count INTEGER,
            track_count INTEGER,
            length_ms INTEGER,
            time_added TEXT,
            in_progress BOOLEAN,
            media_kind TEXT,
            data_kind TEXT,
            uri TEXT,
            artwork_url TEXT
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to insert artist data into the database
def insert_artist(artist):
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Insert artist data into the artists table
    cursor.execute('''
        INSERT OR REPLACE INTO artists (
            id, name, name_sort, album_count, track_count, length_ms, time_added, 
            in_progress, media_kind, data_kind, uri, artwork_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        artist.get('id'),
        artist.get('name'),
        artist.get('name_sort'),
        artist.get('album_count'),
        artist.get('track_count'),
        artist.get('length_ms'),
        artist.get('time_added'),
        artist.get('in_progress'),
        artist.get('media_kind'),
        artist.get('data_kind'),
        artist.get('uri'),
        artist.get('artwork_url')
    ))
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to fetch and process artist data from the API
def fetch_and_store_artists():
    # The URL for the GET request
    url = 'http://192.168.1.13:3689/api/library/artists'
    
    try:
        # Make a GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Iterate through the 'items' array
            if 'items' in data:
                for artist in data['items']:
                    # Insert each artist into the database
                    insert_artist(artist)
                print(f"Inserted {len(data['items'])} artists into the database.")
            else:
                print("'items' key not found in the response")
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
    
    except requests.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Create the database and the artists table
    create_database()
    
    # Fetch and store artist data
    fetch_and_store_artists()

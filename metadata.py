import sqlite3
import re

DATABASE = 'owntone.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_fixed_tracks_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixed_tracks (
            track_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def parse_path(path):
    """
    Parses the file path to extract artist, album, and track information.
    Handles both patterns:
    - /music/Music/{artist}/{album}/{track}
    - /music/Music/{artist}/{track}
    
    Removes leading track number (if it exists) from the track title.
    """
    # Regex for pattern with album: /music/Music/{artist}/{album}/{track}
    match_with_album = re.match(r'^/music/Music/([^/]+)/([^/]+)/([^/]+)$', path)
    
    # Regex for pattern without album: /music/Music/{artist}/{track}
    match_without_album = re.match(r'^/music/Music/([^/]+)/([^/]+)$', path)

    if match_with_album:
        artist, album, track = match_with_album.groups()
        track = remove_track_number(track)  # Remove leading track number
        return artist, album, track
    elif match_without_album:
        artist, track = match_without_album.groups()
        track = remove_track_number(track)  # Remove leading track number
        return artist, None, track
    else:
        return None, None, None

def remove_track_number(track):
    """
    Removes leading track number from the track title if present.
    For example, '01 Track Title' becomes 'Track Title'.
    """
    # Regex to match track number at the start of the title
    match = re.match(r'^\d{1,2}\s+(.*)$', track)
    if match:
        return match.group(1)  # Return the title without the track number
    
    # Regex to match disc and track number at the start of the title
    match = re.match(r'^\d{1,2}\-\d{1,2}\s+(.*)$', track)
    if match:
        return match.group(1)  # Return the title without the track number
    return track  # Return the original title if no match

def normalize_string(s):
    if s is None:
        return ''
    # Strip leading and trailing whitespace, convert to lowercase
    normalized = re.sub(r'\s+', ' ', s.strip()).lower()
    # Remove punctuation
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized

def find_incorrect_tracks(db_file='owntone.db'):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Access rows by column name
    cursor = conn.cursor()
    
    # Select all rows from the tracks table
    cursor.execute("SELECT t.id, t.title, t.artist, t.album, t.path FROM tracks t WHERE NOT EXISTS (SELECT 1 FROM fixed_tracks f WHERE f.track_id = t.id)")
    tracks = cursor.fetchall()
    
    conn.close()
    
    incorrect_tracks = []

    for track in tracks:
        # Parse the path to extract artist, album, and track name
        parsed_artist, parsed_album, parsed_track = parse_path(track['path'])
        
        # Continue only if the path is successfully parsed
        if parsed_artist and parsed_track:
            # Remove file extension from the parsed track name if it exists
            parsed_track = re.sub(r'\.[^.]+$', '', parsed_track)

            # Normalize the parsed values and the track values from the database
            normalized_parsed_artist = normalize_string(parsed_artist)
            normalized_parsed_album = normalize_string(parsed_album) if parsed_album else None
            normalized_parsed_track = normalize_string(parsed_track)

            normalized_db_artist = normalize_string(track['artist'])
            normalized_db_album = normalize_string(track['album'])
            normalized_db_title = normalize_string(track['title'])

            # Compare normalized values
            is_incorrect = False
            if normalized_parsed_artist != normalized_db_artist:
                is_incorrect = True
            if normalized_parsed_album and normalized_parsed_album != normalized_db_album:
                is_incorrect = True
            if normalized_parsed_track != normalized_db_title:
                is_incorrect = True

            # If any of the values don't match, add the row to incorrect_tracks
            if is_incorrect:
                incorrect_tracks.append({
                    'id': track['id'],
                    'title': track['title'],
                    'artist': track['artist'],
                    'album': track['album'],
                    'path': track['path'],
                    'parsed_title': parsed_track,
                    'parsed_artist': parsed_artist,
                    'parsed_album': parsed_album
                })

    conn.close()
    
    return incorrect_tracks

def mark_track_as_fixed(track_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO fixed_tracks (track_id)
        VALUES (?)
    ''', (track_id,))
    conn.commit()
    conn.close()

# Call create_fixed_tracks_table() at the start of your script
create_fixed_tracks_table()

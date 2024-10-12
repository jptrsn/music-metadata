import xml.etree.ElementTree as ET
import os
import sqlite3

def parse_itunes_xml(file_path):
    """
    Parse an iTunes XML file and extract track information.
    
    Args:
        file_path (str): Path to the iTunes XML file.
        
    Returns:
        dict: A dictionary containing track information.
    """
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find the 'dict' element containing track information
    tracks = {}
    track_dict = None

    for dict_element in root.findall("dict/dict/dict"):
        track_info = {}
        current_key = None

        for child in dict_element:
            if child.tag == 'key':
                current_key = child.text
            elif current_key:
                track_info[current_key] = child.text
                current_key = None

        # Add track to the dictionary with its track ID
        if 'Track ID' in track_info:
            track_id = track_info['Track ID']
            tracks[track_id] = track_info

    return tracks

def create_dynamic_database(db_path, all_keys):
    """
    Create a SQLite database dynamically based on all possible keys from the iTunes XML file.
    
    Args:
        db_path (str): Path to the SQLite database file.
        all_keys (set): A set of all keys (fields) across all tracks to define table columns.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Dynamically create table columns based on the keys collected from all tracks
    columns = ', '.join([f"'{key}' TEXT" for key in all_keys])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS itunes_tracks (
            track_id INTEGER PRIMARY KEY,
            {columns}
        )
    ''')

    conn.commit()
    conn.close()

def insert_tracks_into_db(db_path, tracks, all_keys):
    """
    Insert track information into the SQLite database dynamically.
    
    Args:
        db_path (str): Path to the SQLite database file.
        tracks (dict): A dictionary containing track information.
        all_keys (set): A set of all keys (fields) across all tracks.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for track_id, track_info in tracks.items():
        # Ensure that all keys exist in the track info (fill missing fields with None)
        for key in all_keys:
            if key not in track_info:
                track_info[key] = None

        # Dynamically construct the INSERT statement based on track_info keys
        keys = ', '.join([f"'{key}'" for key in track_info.keys()])
        placeholders = ', '.join(['?' for _ in track_info.keys()])
        values = list(track_info.values())

        cursor.execute(f'''
            INSERT OR REPLACE INTO itunes_tracks (
                track_id, {keys}
            ) VALUES (?, {placeholders})
        ''', [track_id] + values)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Get the path of the current directory and the itunes.xml file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    xml_file_path = os.path.join(current_directory, 'itunes.xml')
    db_file_path = os.path.join(current_directory, 'owntone.db')

    # Parse the iTunes XML and extract tracks
    tracks = parse_itunes_xml(xml_file_path)

    # Collect all unique keys (fields) across all tracks
    all_keys = set()
    for track_info in tracks.values():
        all_keys.update(track_info.keys())
    print(f"Captured {len(all_keys)} keys")

    # Create the database and insert the tracks using the collected keys
    if tracks:
        create_dynamic_database(db_file_path, all_keys)
        insert_tracks_into_db(db_file_path, tracks, all_keys)

    print(f"Inserted {len(tracks)} tracks into the database: {db_file_path}")

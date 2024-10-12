import sqlite3

# Function to create the 'track_links' table
def create_track_links_table():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Create the 'track_links' table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS track_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            itunes_track_id INTEGER,
            owntone_track_id INTEGER,
            FOREIGN KEY(itunes_track_id) REFERENCES itunes_tracks(id),
            FOREIGN KEY(owntone_track_id) REFERENCES tracks(id)
        )
    ''')
    
    # Commit and close the connection
    conn.commit()
    conn.close()

# Function to find and insert matching tracks into the 'track_links' table
def find_and_insert_matches():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Join the itunes_tracks and tracks tables based on track title and artist
    cursor.execute('''
        INSERT INTO track_links (itunes_track_id, owntone_track_id)
        SELECT it.track_id AS itunes_track_id, ot.id AS owntone_track_id
        FROM itunes_tracks it
        JOIN tracks ot
        ON it.Name = ot.title
        AND it.Artist = ot.artist
    ''')
    
    # Commit the insert operation
    conn.commit()
    
    # Get the count of matches found and inserted
    rows_inserted = cursor.rowcount
    print(f"{rows_inserted} matches found and inserted into track_links.")
    
    # Close the connection
    conn.close()

# Main function to create the table and find matches
def create_links_for_matching_tracks():
    # Create the 'track_links' table
    create_track_links_table()
    
    # Find and insert matches between the 'itunes_tracks' and 'tracks' tables
    find_and_insert_matches()

if __name__ == "__main__":
    create_links_for_matching_tracks()

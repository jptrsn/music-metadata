import sqlite3
from datetime import datetime

def parse_date(date_str):
    if date_str:
        # Handle the ISO 8601 format
        return int(datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').timestamp())
    return 0

# Function to find and insert matching tracks into the 'track_links' table
def retrieve_itunes_metadata():
    conn = sqlite3.connect('owntone.db')
    cursor = conn.cursor()
    
    # Join the itunes_tracks and track_links tables
    cursor.execute('''
        SELECT tl.owntone_track_id, it.Name, it.Artist, it.`Skip Count`, it.`Skip Date`, it.`Rating`, 
               it.`Date Added`, it.`Play Count`, it.`Play Date` 
        FROM itunes_tracks it
        INNER JOIN track_links tl ON it.track_id = tl.itunes_track_id
    ''')
    
    # Fetch all rows from the query result
    itunes_rows = cursor.fetchall()

    # Close the database connection
    conn.close()

    return itunes_rows


# Function to update the 'files' table in songs3.db with the retrieved data
def update_files_table(itunes_rows):
    conn = sqlite3.connect('songs3.db')
    cursor = conn.cursor()

    for row in itunes_rows:
        owntone_track_id = row[0]
        skip_count = int(row[3]) if row[3] else 0  # Ensure this is an integer
        play_count = int(row[7]) if row[7] else 0  # Ensure this is an integer
        rating = int(row[5]) if row[5] else 0  # Ensure this is an integer
        play_date = int(row[8]) if row[8] else 0
        date_added = parse_date(row[6])
        skip_date = parse_date(row[4])  # Convert to integer timestamp or 0
        
        # Get current values from files table
        cursor.execute("SELECT time_skipped, time_played FROM files WHERE id = ?", (owntone_track_id,))
        current_values = cursor.fetchone()
        
        if current_values:
            current_time_skipped, current_time_played = current_values
            
            # Prepare the time_skipped value
            time_skipped = skip_date if skip_date > current_time_skipped else current_time_skipped
            time_played = play_date if play_date > current_time_played else current_time_played

            cursor.execute('''
                UPDATE files
                SET
                    skip_count = skip_count + ?,
                    play_count = play_count + ?,
                    rating = ? COLLATE BINARY,
                    time_added = ?,
                    time_skipped = ?,
                    time_played = ?
                WHERE id = ?
            ''', (skip_count, play_count, rating, date_added, time_skipped, time_played, owntone_track_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Retrieve iTunes metadata from owntone.db
    itunes_rows = retrieve_itunes_metadata()

    # Update the files table in songs3.db with the retrieved data
    update_files_table(itunes_rows)

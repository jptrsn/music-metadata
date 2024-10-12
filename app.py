from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from metadata import find_incorrect_tracks, mark_track_as_fixed  # Import the function from your metadata script

app = Flask(__name__)
DATABASE = 'owntone.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

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
        SELECT it.Name AS itunes_track_name, it.Artist AS itunes_artist, it.Album AS itunes_album,
               ot.title AS owntone_track_name, ot.artist AS owntone_artist, ot.album AS owntone_album
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

if __name__ == '__main__':
    app.run(port=8000, debug=True)

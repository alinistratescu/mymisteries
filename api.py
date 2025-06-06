import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import os 

import traceback
import json
import re 
import openai


app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('mysteries.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/case/<int:case_id>')
def get_case(case_id):
    conn = get_db_connection()
    case = conn.execute('SELECT * FROM cases WHERE id = ?', (case_id,)).fetchone()
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    clues = conn.execute('SELECT * FROM clues WHERE case_id = ?', (case_id,)).fetchall()
    suspects = conn.execute('SELECT * FROM suspects WHERE case_id = ?', (case_id,)).fetchall()
    timeline = conn.execute('SELECT event FROM timeline WHERE case_id = ?', (case_id,)).fetchall()
    conn.close()
    return jsonify({
        'title': case['title'],
        'background': case['background'],
        'time': case['time'],
        'clues': [dict(c) for c in clues],
        'suspects': [dict(s) for s in suspects],
        'timeline': [t['event'] for t in timeline]
    })

@app.route('/api/cases', methods=['POST'])
def add_case():
    data = request.get_json()
    title = data.get('title')
    desc = data.get('desc')
    img = data.get('img')
    clues = data.get('clues', [])
    timeline = data.get('timeline', [])
    real_killer = data.get('realKiller')
    if not (title and desc and img and real_killer):
        return jsonify({'success': False, 'error': 'Missing fields'}), 400
    conn = get_db_connection()
    # Insert into cases table (add columns if needed)
    conn.execute('INSERT INTO cases (title, background, time) VALUES (?, ?, ?)', (title, desc, ''))
    case_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    # Insert a default clue as thumbnail (optional, for dashboard display)
    conn.execute('INSERT INTO clues (case_id, img, title, desc) VALUES (?, ?, ?, ?)', (case_id, img, 'Thumbnail', desc))
    for clue in clues:
        conn.execute('INSERT INTO clues (case_id, img, title, desc) VALUES (?, ?, ?, ?)', (case_id, clue.get('img',''), clue.get('title',''), clue.get('desc','')))
    for event in timeline:
        conn.execute('INSERT INTO timeline (case_id, event) VALUES (?, ?)', (case_id, event))
    # Store the real killer in a new table or as a field in cases (here, as a new table for flexibility)
    conn.execute('CREATE TABLE IF NOT EXISTS real_killer (case_id INTEGER, name TEXT)')
    conn.execute('INSERT INTO real_killer (case_id, name) VALUES (?, ?)', (case_id, real_killer))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': case_id})

@app.route('/api/cases')
def get_cases():
    conn = get_db_connection()
    cases = conn.execute('SELECT id, title, background, time FROM cases').fetchall()
    # Optionally add thumbnail and short desc columns to your DB, else use background as desc
    result = []
    for c in cases:
        # Try to get a thumbnail and desc from clues or use defaults
        img = conn.execute('SELECT img FROM clues WHERE case_id = ? LIMIT 1', (c['id'],)).fetchone()
        result.append({
            'id': c['id'],
            'title': c['title'],
            'desc': c['background'][:80] + ('...' if len(c['background']) > 80 else ''),
            'img': img['img'] if img else 'https://via.placeholder.com/400x140?text=No+Image'
        })
    conn.close()
    return jsonify(result)

@app.route('/api/generate_case', methods=['POST'])
def generate_case():
    prompt = (
        "Generate a random detective mystery case as a JSON object with the following fields: "
        "title (string), desc (string), img (string, a plausible image URL), clues (list of objects with title, desc, img), "
        "timeline (list of strings), suspects (list of objects with name, relation, age, motive, alibi, notes, img), "
        "realKiller (string, must match one suspect's name). "
        "Make it creative, plausible, and fun. Use realistic names and details. Example image URLs can be from unsplash or randomuser.me."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=1.1,
        )
        text = response.choices[0].message.content
        print("=== AI returned text ===")
        print(text)

        json_match = re.search(r'{.*}', text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in AI response.")
        
        case_data = json.loads(json_match.group(0))

        required_fields = ['title', 'desc', 'img', 'realKiller', 'suspects']
        for field in required_fields:
            if field not in case_data or not case_data[field]:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        title = case_data['title']
        desc = case_data['desc']
        img = case_data['img']
        clues = case_data.get('clues', [])
        timeline = case_data.get('timeline', [])
        real_killer = case_data['realKiller']
        suspects = case_data['suspects']

        conn = get_db_connection()
        conn.execute('INSERT INTO cases (title, background, time) VALUES (?, ?, ?)', (title, desc, ''))
        case_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        conn.execute('INSERT INTO clues (case_id, img, title, desc) VALUES (?, ?, ?, ?)', (case_id, img, 'Thumbnail', desc))

        for clue in clues:
            conn.execute(
                'INSERT INTO clues (case_id, img, title, desc) VALUES (?, ?, ?, ?)',
                (case_id, clue.get('img', ''), clue.get('title', ''), clue.get('desc', ''))
            )

        for event in timeline:
            conn.execute('INSERT INTO timeline (case_id, event) VALUES (?, ?)', (case_id, event))

        for s in suspects:
            conn.execute(
                'INSERT INTO suspects (case_id, img, name, age, relation, alibi, notes, motive) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    case_id,
                    s.get('img', ''),
                    s.get('name', ''),
                    s.get('age', 0),
                    s.get('relation', ''),
                    s.get('alibi', ''),
                    s.get('notes', ''),
                    s.get('motive', ''),
                )
            )

        conn.execute('CREATE TABLE IF NOT EXISTS real_killer (case_id INTEGER, name TEXT)')
        conn.execute('INSERT INTO real_killer (case_id, name) VALUES (?, ?)', (case_id, real_killer))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'id': case_id})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/real_killer/<int:case_id>')
def get_real_killer(case_id):
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS real_killer (case_id INTEGER, name TEXT)')
    killer = conn.execute('SELECT name FROM real_killer WHERE case_id = ?', (case_id,)).fetchone()
    conn.close()
    if killer:
        return jsonify({'name': killer['name']})
    else:
        return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)

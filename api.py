import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
import os 

import traceback
import json
import re 
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")


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
        print("=== Prompt Sent to AI ===")
        print(prompt)

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=1.1,
        )
        print("=== Raw Response from AI ===")
        print(response)

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
        print("=== Exception Occurred ===")
        print(str(e))
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

@app.route('/api/generate_new_case', methods=['POST'])
def generate_new_case():
    prompt = (
        "You are an expert narrative designer for mystery and detective games.\n\n"
        "Based on the following game structure, generate an entirely new, richly detailed case with unique characters, a compelling crime, and multiple suspects with motives and hidden connections. The story should unfold in 5 stages, each with a specific investigation focus, with suspects, clues, and actions evolving stage-by-stage. Include a final stage where the player must make a key decision about who is truly guilty.\n\n"
        "Follow this JSON structure:\n\n"
        "{\n"
        "  \"stages\": [\n"
        "    {\n"
        "      \"name\": \"Stage Name\",\n"
        "      \"description\": \"Brief but atmospheric summary of what happens in this stage.\",\n"
        "      \"actions\": [\"Action 1\", \"Action 2\", \"...\"],\n"
        "      \"action_clues\": {\n"
        "        \"index\": [{ \"description\": \"Clue text\", \"location\": \"Where the clue is found\" }]\n"
        "      },\n"
        "      \"action_suspects\": {\n"
        "        \"index\": [\n"
        "          {\n"
        "            \"name\": \"Suspect Name\",\n"
        "            \"role\": \"Job or connection to crime\",\n"
        "            \"motive\": \"Their possible reason for being involved\",\n"
        "            \"notes\": \"Other behavioral or narrative observations\"\n"
        "          }\n"
        "        ]\n"
        "      }\n"
        "    },\n"
        "    \"...more stages...\"\n"
        "  ],\n"
        "  \"suspects\": [\n"
        "    { \"id\": 1, \"name\": \"Suspect 1\" },\n"
        "    { \"id\": 2, \"name\": \"Suspect 2\" },\n"
        "    \"...more suspects...\"\n"
        "  ],\n"
        "  \"endings\": [\n"
        "    {\n"
        "      \"type\": \"true\",\n"
        "      \"suspectId\": X,\n"
        "      \"summary\": \"The correct ending with true mastermind revealed.\"\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"alternate\",\n"
        "      \"suspectId\": X,\n"
        "      \"summary\": \"A plausible but incorrect ending with consequences.\"\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"secret\",\n"
        "      \"suspectId\": X,\n"
        "      \"summary\": \"A hidden resolution based on deeper investigation.\"\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"red herring\",\n"
        "      \"suspectId\": X,\n"
        "      \"summary\": \"A misleading ending based on false assumptions.\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n\n"
        "    The mystery must revolve around a valuable or meaningful object, person, or secret that has been stolen, sabotaged, or gone missing.\n\n"
        "    Introduce at least 4 suspects with complex motives and evolving stories.\n\n"
        "    Use clues and suspect behaviors to build tension across stages.\n\n"
        "    The final stage should provide multiple plausible conclusions.\n\n"
        "    Use evocative, cinematic language for descriptions.\n\n"
        "Output only a valid JSON formatted according to the structure above."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=1.1,
        )
        print("=== Raw Response from AI ===")
        print(response)

        text = response.choices[0].message.content
        print("=== AI returned text ===" + text)

        json_match = re.search(r'{.*}', text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in AI response.")

        case_data = json.loads(json_match.group(0))
        return jsonify({'success': True, 'case': case_data})

    except Exception as e:
        print("=== Exception Occurred ===")
        print(str(e))
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

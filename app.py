from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import openai
import os

app = Flask(__name__)
app.secret_key = "Your Open api key"
openai.api_key = "Your Open api key"


# Initialize SQLite database
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    invalid_credentials = False
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        if cur.fetchone():
            session['user'] = user
            return redirect(url_for('select_language'))
        else:
            invalid_credentials = True
    return render_template('login.html', invalid_credentials=invalid_credentials)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        con = sqlite3.connect("database.db")
        con.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
        con.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/select_language', methods=['GET', 'POST'])
def select_language():
    if request.method == 'POST':
        session['language'] = request.form['language']
        return redirect(url_for('chatbot'))
    return render_template('select_language.html')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = ""
    if request.method == 'POST':
        user_input = request.form['query']
        language = session.get('language', 'english')
        response = ask_chatgpt(user_input, language)
    else:
        language = session.get('language', 'english')
    return render_template('chatbot.html', response=response, language=language)

def ask_chatgpt(prompt, language):
    mining_keywords = [
        "mining", "coal", "dgms", "regulation", "explosives", "colliery",
        "wages", "circulars", "cba", "la", "randr", "act", "rules",
        "payment", "mines", "proceedings", "dgms circulars", "land acquisition"
    ]
    if not any(keyword.lower() in prompt.lower() for keyword in mining_keywords):
        return "Sorry, I can only help with mining-related Acts, Rules, and Regulations."

    language_prefix = {
        "english": "Answer in English: ",
        "hindi": "हिंदी में उत्तर दें: ",
        "telugu": "తెలుగులో సమాధానం ఇవ్వండి: ",
        "kannada": "ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರ ನೀಡಿ: "
    }
    full_prompt = language_prefix.get(language, '') + prompt

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": full_prompt}]
    )
    return response['choices'][0]['message']['content']

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedback_text = request.form['feedback']

        # Optional: Store feedback to a database or log file
        # For example: save_to_db(feedback_text)

        flash("Thank you for your feedback!", "success")
        return redirect(url_for('login'))  # Redirect to login page

    return render_template('feedback.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Run app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)



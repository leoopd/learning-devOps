from flask import Flask, request, render_template
import openai
import os
import sqlite3

# The OpenAI Key is stored in ~/.zshrc
openai.api_key = os.environ["OPENAI_API_KEY"]

app = Flask(__name__)
user_input = ''
user_rating = 0
outpu = ''

def init_db():
    connection = sqlite3.connect('conversations.db')
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            prompt TEXT,
            response TEXT,
            rating INTEGER
        )
    """)
    connection.commit()
    connection.close()

@app.before_first_request
def before_first_request():
    init_db()

# Will process the webapp with the model and settings specified.
@app.route('/', methods=['GET', 'POST'])
def scs_ai():
    global user_input
    global user_rating
    global output
    if request.method == 'POST':

        # If user fills the rating-textbox write the rating to the database.
        if user_input:
            user_rating = int(request.form['user_rating'])
            connection = sqlite3.connect('conversations.db')
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE conversations
                SET rating = ?
                WHERE prompt = ? AND response = ?
            """, (user_rating, user_input, output))
            connection.commit()
            connection.close()
            return render_template('ai_templates.html')

        # If user fills the prompt-textbox create a response, return it and write user_input
        # and response to the database.
        user_input = 'Domains, ' + request.form['user_input'] + '\'\\n\\n###\\n\\n'

        response = openai.Completion.create(
            engine='curie:ft-personal:scs-faq-domains-2023-04-13-09-28-43',
            prompt=user_input,
            max_tokens=300,
            n=1,
            stop=[" ###"],
            frequency_penalty=1
        )
            
        output = response.choices[0].text.strip()
        user_rating = None

        connection = sqlite3.connect('conversations.db')
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO conversations (prompt, response) 
            VALUES (?, ?)
            """, (user_input, output))
        connection.commit()
        connection.close()

        return render_template('ai_templates.html', output=output, user_input=user_input, user_rating=user_rating)
    else:
        return render_template('ai_templates.html')         

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


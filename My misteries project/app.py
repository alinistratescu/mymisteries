from flask import Flask, render_template, request

app = Flask(__name__)

mystery_text = "A priceless painting has disappeared from the museum. Can you figure out who took it?"
suspects = [
    "The night guard",
    "The curator",
    "The visitor"
]

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/mystery', methods=['GET', 'POST'])
def play_mystery():
    result = None
    if request.method == 'POST':
        choice = request.form.get('suspect')
        if choice == '2':
            result = "Correct! The curator had the keys and was acting suspiciously."
        else:
            result = "That's not correct. Try again!"
    return render_template('mystery.html', mystery_text=mystery_text, suspects=suspects, result=result)

if __name__ == '__main__':
    app.run(debug=True)

import os
import sqlite3
from flask import Flask
from flask import Flask, render_template


app = Flask(__name__)
app.secret_key = "nagyon-titkos-kulcs"

def init_db():
    if not os.path.exists("raktar.db"):
        conn = get_db_connection()
        with open("raktar.sql", "r", encoding="utf8") as f:
                conn.executescript(f.read())
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(app.config["raktar.db"])
    conn.row_factory = sqlite3.Row
    return conn

init_db()

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
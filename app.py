import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash


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
    conn = sqlite3.connect("raktar.db")
    conn.row_factory = sqlite3.Row
    return conn

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/butorok")
def butor_list():
     conn = get_db_connection()
     rows = conn.execute("SELECT * FROM butor ORDER BY cikkszam").fetchall()
     conn.close()
     return render_template("butor_list.html", butorok=rows)


@app.route("/butor/uj", methods=["GET", "POST"])
def butor_create():
    if request.method == "POST":
        cikkszam = request.form.get("cikkszam", "").strip()
        nev = request.form.get("nev", "").strip()
        suly = request.form.get("suly", "").strip()
        x = request.form.get("x", "").strip()
        y = request.form.get("y", "").strip()
        z = request.form.get("z", "").strip()


        if not cikkszam:
            flash("A cikkszám nem lehet üres!", "Hiba")
            return redirect(url_for("butor_create"))


        conn = get_db_connection()
        existing = conn.execute("SELECT * FROM butor WHERE cikkszam = ?", (cikkszam,)).fetchone()
        if existing:
            conn.close()
            flash("Ez a cikkszám már létezik!", "Hiba")
            return redirect(url_for("butor_create"))



        conn.execute("INSERT INTO butor (cikkszam, nev, suly, x, y, z) VALUES (?, ?, ?, ?, ?, ?)",(cikkszam, nev, suly, x, y, z))
        conn.commit()
        conn.close()


        flash("Új bútor sikeresen hozzáadva!", "Sikeres")
    return render_template("butor_form.html")

@app.route("/butor/<cikkszam>/szerkeszt", methods=["GET", "POST"])
def butor_edit(cikkszam):
    conn = get_db_connection()


    if request.method == "GET":
        row = conn.execute("SELECT * FROM butor WHERE cikkszam = ?", (cikkszam,)).fetchone()
        conn.close()

        if row is None:
            flash("A megadott cikkszám nem található!", "Hiba")
            return redirect(url_for("butor_list"))

        return render_template(
            "butor_form.html",
            mode="edit",
            cikkszam=row["cikkszam"],
            nev=row["nev"],
            suly=row["suly"],
            x=row["x"],
            y=row["y"],
            z=row["z"]
        )

    nev = request.form.get("nev", "").strip()
    suly = request.form.get("suly", "").strip()
    x = request.form.get("x", "").strip()
    y = request.form.get("y", "").strip()
    z = request.form.get("z", "").strip()

    conn.execute(
        "UPDATE butor SET nev = ?, suly = ?, x = ?, y = ?, z = ? WHERE cikkszam = ?",
        (nev, suly, x, y, z, cikkszam)
    )
    conn.commit()
    conn.close()

    flash("A bútor módosítása sikeres volt!", "Siker")
    return redirect(url_for("butor_list"))

@app.route("/butor/<cikkszam>/torol", methods=["POST"])
def butor_delete(cikkszam):
    conn = get_db_connection()

    conn.execute("DELETE FROM raktarkeszlet WHERE cikkszam = ?", (cikkszam,))

    conn.execute("DELETE FROM armatrix WHERE cikkszam = ?", (cikkszam,))

    conn.execute("DELETE FROM butor WHERE cikkszam = ?", (cikkszam,))

    conn.commit()
    conn.close()

    flash("A bútor és a kapcsolt rekordok törlése sikeres volt!", "Siker")
    return redirect(url_for("butor_list"))



if __name__ == "__main__":
    app.run(debug=True)
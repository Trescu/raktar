import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "nagyon-titkos-kulcs"


#-------------------------------------------------------
# DB kapcsolat
#-------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect("raktar.db")
    conn.row_factory = sqlite3.Row
    return conn


#-------------------------------------------------------
# DB inicializálás (Flask 3.x kompatibilis)
#-------------------------------------------------------
def init_db():
    if not os.path.exists("raktar.db"):
        conn = get_db_connection()
        with open("raktar.sql", "r", encoding="utf8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# Inicializáljuk induláskor (Flask 3.x ajánlott mód)
init_db()


#-------------------------------------------------------
# 1. Főoldal
#-------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


#-------------------------------------------------------
# 2. Bútorok listája + keresés
#-------------------------------------------------------
@app.route("/butorok")
def butor_list():
    q = request.args.get("q", "")

    conn = get_db_connection()
    if q:
        rows = conn.execute(
            "SELECT * FROM butor WHERE nev LIKE ? ORDER BY cikkszam",
            (f"%{q}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM butor ORDER BY cikkszam"
        ).fetchall()

    conn.close()
    return render_template("butor_list.html", butorok=rows, q=q)


#-------------------------------------------------------
# 3. Új bútor
#-------------------------------------------------------
@app.route("/butor/uj", methods=["GET", "POST"])
def butor_create():
    if request.method == "POST":
        cikkszam = request.form["cikkszam"].strip()
        nev = request.form["nev"].strip()
        suly = request.form["suly"]
        x = request.form["x"]
        y = request.form["y"]
        z = request.form["z"]

        if not cikkszam:
            flash("A cikkszám kötelező!", "danger")
            return redirect(url_for("butor_create"))

        conn = get_db_connection()
        exists = conn.execute(
            "SELECT 1 FROM butor WHERE cikkszam = ?", (cikkszam,)
        ).fetchone()
        if exists:
            flash("Már létezik ilyen cikkszám!", "danger")
            conn.close()
            return redirect(url_for("butor_create"))

        conn.execute(
            "INSERT INTO butor (cikkszam, nev, suly, x, y, z) VALUES (?, ?, ?, ?, ?, ?)",
            (cikkszam, nev, float(suly), int(x), int(y), int(z))
        )
        conn.commit()
        conn.close()

        flash("Új bútor felvéve!", "success")
        return redirect(url_for("butor_list"))

    return render_template("butor_form.html", mode="create")


#-------------------------------------------------------
# 4. Bútor módosítása
#-------------------------------------------------------
@app.route("/butor/<cikkszam>/szerkeszt", methods=["GET", "POST"])
def butor_edit(cikkszam):
    conn = get_db_connection()

    if request.method == "POST":
        nev = request.form["nev"]
        suly = request.form["suly"]
        x = request.form["x"]
        y = request.form["y"]
        z = request.form["z"]

        conn.execute(
            """UPDATE butor 
               SET nev=?, suly=?, x=?, y=?, z=?
               WHERE cikkszam=?""",
            (nev, float(suly), int(x), int(y), int(z), cikkszam)
        )
        conn.commit()
        conn.close()

        flash("Bútor módosítva!", "success")
        return redirect(url_for("butor_list"))

    row = conn.execute(
        "SELECT * FROM butor WHERE cikkszam = ?", (cikkszam,)
    ).fetchone()

    conn.close()

    if not row:
        flash("Nincs ilyen bútor!", "danger")
        return redirect(url_for("butor_list"))

    return render_template("butor_form.html", mode="edit", butor=row)


#-------------------------------------------------------
# 5. Bútor törlése
#-------------------------------------------------------
@app.route("/butor/<cikkszam>/torol", methods=["POST"])
def butor_delete(cikkszam):
    conn = get_db_connection()

    conn.execute("DELETE FROM raktarkeszlet WHERE cikkszam=?", (cikkszam,))
    conn.execute("DELETE FROM armatrix WHERE cikkszam=?", (cikkszam,))
    conn.execute("DELETE FROM butor WHERE cikkszam=?", (cikkszam,))
    conn.commit()
    conn.close()

    flash("Bútor törölve!", "success")
    return redirect(url_for("butor_list"))


#-------------------------------------------------------
# 6. Árlista
#-------------------------------------------------------
@app.route("/arak")
def price_list():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT b.cikkszam, b.nev, a.lista_ar, a.akcios_ar
        FROM butor b
        LEFT JOIN armatrix a ON a.cikkszam = b.cikkszam
        ORDER BY b.cikkszam
    """).fetchall()
    conn.close()
    return render_template("price_list.html", sorok=rows)


#-------------------------------------------------------
# 7. Árak frissítése
#-------------------------------------------------------
@app.route("/arak/<cikkszam>", methods=["POST"])
def update_price(cikkszam):
    lista_ar = request.form["lista_ar"]
    akcios_ar = request.form["akcios_ar"]

    # HA NEM SZÁM, LEGYEN NULL  <-- EZ A FONTOS FIX
    if lista_ar.strip() == "" or lista_ar == "None":
        lista_ar = None
    if akcios_ar.strip() == "" or akcios_ar == "None":
        akcios_ar = None

    conn = get_db_connection()

    exists = conn.execute(
        "SELECT 1 FROM armatrix WHERE cikkszam=?", (cikkszam,)
    ).fetchone()

    if exists:
        conn.execute(
            "UPDATE armatrix SET lista_ar=?, akcios_ar=? WHERE cikkszam=?",
            (lista_ar, akcios_ar, cikkszam)
        )
    else:
        conn.execute(
            "INSERT INTO armatrix (cikkszam, lista_ar, akcios_ar) VALUES (?, ?, ?)",
            (cikkszam, lista_ar, akcios_ar)
        )

    conn.commit()
    conn.close()

    flash("Árak módosítva!", "success")
    return redirect(url_for("price_list"))



#-------------------------------------------------------
# 8. Raktárkészlet lista + szűrés
#-------------------------------------------------------
@app.route("/keszlet")
def stock():
    conn = get_db_connection()

    raktar_filter = request.args.get("raktar")

    raktarak = conn.execute("SELECT * FROM raktar").fetchall()

    if raktar_filter:
        rows = conn.execute("""
            SELECT r.nev AS raktar_nev, k.cikkszam, b.nev, k.mennyiseg
            FROM raktarkeszlet k
            JOIN raktar r ON r.id = k.raktarID
            JOIN butor b ON b.cikkszam = k.cikkszam
            WHERE r.id = ?
            ORDER BY r.nev, b.nev
        """, (raktar_filter,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT r.nev AS raktar_nev, k.cikkszam, b.nev, k.mennyiseg
            FROM raktarkeszlet k
            JOIN raktar r ON r.id = k.raktarID
            JOIN butor b ON b.cikkszam = k.cikkszam
            ORDER BY r.nev, b.nev
        """).fetchall()

    conn.close()
    return render_template("stock.html", sorok=rows, raktarak=raktarak, selected=raktar_filter)


#-------------------------------------------------------
# 9. Pandas riport – TOP 10 térfogat
#-------------------------------------------------------
@app.route("/report/top-terfogat")
def report_top_volume():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM butor", conn)
    conn.close()

    if df.empty:
        html_table = "<p>Nincs adat.</p>"
    else:
        df["terfogat"] = df["x"] * df["y"] * df["z"]
        df = df.sort_values("terfogat", ascending=False).head(10)
        html_table = df.to_html(classes="table table-striped")

    return render_template("report.html", table=html_table)


#-------------------------------------------------------
# 10. Demo seed (nem publikus)
#-------------------------------------------------------
@app.route("/dev/seed")
def dev_seed():
    conn = get_db_connection()

    conn.execute("INSERT OR IGNORE INTO butor VALUES ('A1','Szekrény',30,100,50,200)")
    conn.execute("INSERT OR IGNORE INTO butor VALUES ('A2','Asztal',15,120,80,75)")
    conn.execute("INSERT OR IGNORE INTO raktarkeszlet (raktarID,cikkszam,mennyiseg) VALUES (1,'A1',5)")
    conn.execute("INSERT OR IGNORE INTO raktarkeszlet (raktarID,cikkszam,mennyiseg) VALUES (2,'A2',3)")
    conn.commit()
    conn.close()

    return "Seeder lefutott!"


#-------------------------------------------------------
# Futtatás
#-------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request
from datetime import datetime
import random

app = Flask(__name__)

@app.route("/")
def acceuil():
    return render_template("acceuil.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/base", methods=["GET", "POST"])
def base():
    heure = datetime.now().strftime("%H:%M:%S")
    nombre = random.randint(1, 100)
    resultat = None

    # Si un formulaire a été soumis
    if request.method == "POST":
        try:
            a = float(request.form.get("a", 0))
            b = float(request.form.get("b", 0))
            resultat = a + b
        except ValueError:
            resultat = "Erreur de saisie"

    return render_template("base.html", heure=heure, nombre=nombre, resultat=resultat)

if __name__ == "__main__":
    app.run(debug=True)
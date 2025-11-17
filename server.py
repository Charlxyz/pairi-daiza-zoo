from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bdd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '\xf0?a\x9a\\\xff\xd4;\x0c\xcbHi'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin): # Définir le modèle User
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # user, soigneur, admin

    def __repr__(self):
        return f'<User {self.nom}>'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)        
    return decorated_function

@login_manager.user_loader # Charge l'utilisateur si il se connecte
def load_user(id):
    return db.session.get(User, int(id))

@app.route("/")
def acceuil():
    return render_template("accueil.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/login', methods=['POST', 'GET']) # Page de connexion
def login():
    if current_user.is_authenticated:
        flash('Vous etes deja connecter !', 'danger')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            email = request.form['identifiant'] # Récupere l'email inscrit dans le html
            password = request.form['mdp'] # Récupere le mot de passe inscrit dans le html
            print(email)
            print(password)
            if all(value not in ["", None, " "] for value in [email, password]):
                user = User.query.filter_by(email=email).first() # Verrifie l'existance de l'adresse mail dans la base de donnee
                if user and bcrypt.check_password_hash(user.password, password): # check_password_hash() permet de comparé le mot de passe dans la base de donnees et celui rentre dans le html
                    login_user(user) # Connecte l'utilisateur on peut rajouter remember=True pour le garder connecter meme si il ferme son navigateur
                    flash("Connexion réussie !", 'success')
                    return redirect(url_for('index')) # Redirige a la fonction index
                else:
                    flash('Identifiants incorrects', 'danger')
            else:
                flash("Des informations sont manquantes.", 'danger')

    return render_template("login.html")

@app.route('/inscription', methods=['POST', 'GET']) # Page d'inscription
def register():
    if current_user.is_authenticated:
        flash("Vous etes deja connecter", "default")
        return redirect(url_for('index'))
    else:
        if request.method == "POST":
            nom = request.form['nom'] # Récupere le nom d'utilisateur inscrit dans le html
            email = request.form['email'] # Récupere l'email inscrit dans le html
            password = request.form['mdp'] # Récupere le mot de passe inscrit dans le html
            check_password = request.form['mdp2'] # Récupere le le deuxieme mot de passe inscrit dans le html

            print(nom, email, password, check_password)

            nom_exists = User.query.filter_by(nom=nom).first() # Verrifie si le nom d'utlisateur existe deja
            email_exists = User.query.filter_by(email=email).first() # Verrifie si l'adresse mail existe deja
            
            if nom_exists:
                flash(f"{nom} est dejà utiliser.", 'danger')
            elif email_exists:
                flash(f"{email} est dejà utiliser.", 'danger')
            elif password != check_password: # Verrifie si les deux mot de passe rentrés sont identiques
                flash("Les mots de passe ne sont pas identiques.", 'danger')
            else:
                if all(value not in ["", None, " "] for value in [nom, email, password]):
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8') # Hash le mot de passe de l'utilisateur pour le rendre indécriptable
                    user = User(
                        nom=nom,
                        email=email,
                        password=hashed_password,
                        role='user'
                        )
                    db.session.add(user) # Ajoute l'utilisateur a la base de donnes bdd.bd
                    db.session.commit()
                    flash("Compte créé. Veuillez vous connecter.", 'success')
                    return redirect(url_for('login'))
                
                flash("Des informations sont manquantes.", 'danger')

            return redirect(url_for('register'))

    return render_template("inscription.html")

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    pass

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
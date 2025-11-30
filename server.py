import random
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
from werkzeug.utils import secure_filename
import os, uuid
from datetime import datetime
import qrcode
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bdd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '\xf0?a\x9a\\\xff\xd4;\x0c\xcbHi'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

# UPLOAD FOLDER CONFIGURATION
UPLOAD_FOLDER_ANIMAL = "static/uploads"
ALLOWED_EXTENSIONS_ANIMAL = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_ANIMAL

class User(db.Model, UserMixin): # Définir le modèle User
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    prenom = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # user, soigneur, admin

    def __repr__(self):
        return f'<User {self.nom}>'
    
class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    enclot = db.Column(db.String(80), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    espèce = db.Column(db.String(80), nullable=False)
    arrive = db.Column(db.String(80), nullable=False)
    depart = db.Column(db.String(80))
    soin = db.Column(db.String(80))
    image = db.Column(db.String(200))

    # AJOUT ICI : Supprimer automatiquement les soins liés
    soins = db.relationship(
        "Soin",
        backref="animal",
        cascade="all, delete-orphan",
        lazy=True
    )

class Event(db.Model): # Définir le modèle Event
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    start = db.Column(db.String(50))
    end = db.Column(db.String(50))

class Tickets(db.Model): # Définir le modèle Tickets
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    validite = db.Column(db.String(50), nullable=False)
    date_visite = db.Column(db.String(50), nullable=False)
    categorie = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Soin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    categorie = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)

    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    soigneur_id = db.Column(db.Integer, db.ForeignKey('soigneur.id'), nullable=False)

    # Plus besoin de définir "animal = relationship(...)"
    soigneur = db.relationship('Soigneur', backref='soins', lazy=True)

class Soigneur(db.Model): # Définir le modèle Soigneur
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vous devez être connecté pour accéder à cette page.", 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)        
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_ANIMAL

@login_manager.user_loader # Charge l'utilisateur si il se connecte
def load_user(id):
    return db.session.get(User, int(id))

@app.template_filter('date_humaine')
def date_humaine(value):
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d")
    return value.strftime("%d %B %Y")  # ex : 27 novembre 2025

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
        return redirect(url_for('acceuil'))
    else:
        if request.method == 'POST':
            email = request.form['identifiant'] # Récupere l'email inscrit dans le html
            password = request.form['mdp'] # Récupere le mot de passe inscrit dans le html
            if all(value not in ["", None, " "] for value in [email, password]):
                user = User.query.filter_by(email=email).first() # Verrifie l'existance de l'adresse mail dans la base de donnee
                if user and bcrypt.check_password_hash(user.password, password): # check_password_hash() permet de comparé le mot de passe dans la base de donnees et celui rentre dans le html
                    login_user(user) # Connecte l'utilisateur on peut rajouter remember=True pour le garder connecter meme si il ferme son navigateur
                    flash("Connexion réussie !", 'success')
                    return redirect(url_for('acceuil')) # Redirige a la fonction index
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
            prenom = request.form['prenom'] if request.form['prenom'] else "" # Récupere le prenom d'utilisateur inscrit dans le html
            email = request.form['email'] # Récupere l'email inscrit dans le html
            password = request.form['mdp'] # Récupere le mot de passe inscrit dans le html
            check_password = request.form['mdp2'] # Récupere le le deuxieme mot de passe inscrit dans le html

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
                        prenom=prenom,
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Déconnexion réussie.", 'success')
    return redirect(url_for('acceuil'))

@app.route('/ticket/<string:ticket_uuid>/qrcode')
@login_required
def ticket_qrcode(ticket_uuid):
    
    if ticket_uuid in ['', None]:
        flash("Votre QR Code n'est pas valide", 'erreur')
        return redirect(url_for('acceuil'))
    
    # Génération du QR code en mémoire
    img = qrcode.make(ticket_uuid)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png')

@app.route("/compte")
@login_required
def compte():
    tickets = Tickets.query.filter_by(user_id=current_user.id).all()
    return render_template("compte.html", tickets=tickets)

@app.route("/checktickets")
@login_required
def checktickets():
    if current_user.role != 'admin':
        flash("Vous n'avez pas les permissions pour accéder a cette page", 'danger')
        return redirect(url_for('acceuil'))
    
    return render_template("checktickets.html")

@app.route('/check_ticket/<string:ticket_uuid>')
@login_required
def check_ticket(ticket_uuid):
    if current_user.role != 'admin':
        flash("Vous n'avez pas les permissions pour accéder a cette page", 'danger')
        return redirect(url_for('acceuil'))

    ticket = Tickets.query.filter_by(uuid=ticket_uuid).first()
    
    # Ticket non trouvé
    if ticket is None:
        return jsonify({
            "valid": False,
            "message": "Ticket introuvable"
        }), 404
    
    # Ticket déjà usé
    if ticket.validite == "False":
        return jsonify({
            "valid": False,
            "message": "Ticket déjà utilisé"
        })
    
    # Vérifier si la date est valide
    date_visite = datetime.strptime(ticket.date_visite, "%Y-%m-%d").date()
    today = datetime.now().date()
    
    if date_visite != today:
        return jsonify({
            "valid": False,
            "type": "date_invalid",
            "message": f"Prévu pour {date_visite.strftime('%d/%m/%Y')}"
        })
    
    # Ticket valide : le marquer comme usé et retourner succès
    ticket.validite = "False"
    db.session.commit()
    
    return jsonify({
        "valid": True,
        "message": "Ticket accepté",
        "nom": ticket.nom,
        "prenom": ticket.prenom,
        "categorie": ticket.categorie
    })

@app.route("/book")
def book():
    return render_template("reserver.html")

@app.route('/animals')
def animal():
    zone = request.args.get('zone')

    if zone:
        animaux = Animal.query.filter(Animal.zone.ilike(f"%{zone}%")).all()
        return render_template("animaux.html", animaux=animaux, zone=zone)

    if current_user.is_authenticated and current_user.role in ['admin', 'soigneur']:
        animaux = Animal.query.all()
        return render_template("animaux.html", animaux=animaux, zone=None)

    categories = ['Cascade', 'Montagne', 'Afrique', 'Savane', 'Sahara']
    resultats = []

    for cat in categories:
        count = Animal.query.filter(Animal.zone == cat).count()
        if count > 0:
            choix = random.randint(0, count - 1)
            animal = (
                Animal.query
                .filter(Animal.zone == cat)
                .offset(choix)
                .first()
            )
            if animal:
                resultats.append(animal)

    return render_template("animaux.html", animaux=resultats, zone=None)

@app.route('/api/addanimal', methods=['POST'])
@login_required
def add_animals():
    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à ajouter des animaux.", 'danger')
        return redirect(url_for('animal'))

    nom = request.form['nom']
    race = request.form['race']
    enclot = request.form['enclot']
    arrive = request.form['arrive']
    zone = request.form['zone']

    depart = request.form.get('depart')

    image = request.files.get('file')
    image_filename = None

    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        image_filename = filename

    nouvel_animal = Animal(
        nom=nom,
        espèce=race,
        enclot=enclot,
        zone=zone,
        arrive=arrive,
        depart=depart,
        image=image_filename
    )
    db.session.add(nouvel_animal)
    db.session.commit()
    flash("Animal ajouté avec succès.", 'success')

    return redirect(url_for('animal'))


@app.route('/api/deleteanimal/<int:animal_id>', methods=['DELETE', 'GET', 'POST'])
@login_required
def delete_animal(animal_id):
    if request.method != 'DELETE':
        flash('Méthode non autorisée.', 'danger')
        return redirect(url_for('animal'))

    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à supprimer cet animal.", 'danger')
        return redirect(url_for('animal'))

    animal = db.session.get(Animal, animal_id)
    if not animal:
        flash('Animal non trouvé.', 'erreur')
        return redirect(url_for('animal'))

    # remove image file if exists
    try:
        if animal.image:
            image_path = os.path.join(app.root_path, app.config.get('UPLOAD_FOLDER', 'static/uploads'), animal.image)
            if os.path.exists(image_path):
                os.remove(image_path)
    except Exception:
        pass

    db.session.delete(animal)
    db.session.commit()
    flash('Animal supprimé avec succès.', 'success')

    return jsonify({"success": True}), 200

@app.route('/api/editanimal/<int:animal_id>', methods=['POST'])
@login_required
def edit_animal(animal_id):
    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à modifier cet animal.", 'danger')
        return redirect(url_for('animal'))

    animal = db.session.get(Animal, animal_id)
    if not animal:
        flash('Animal non trouvé.', 'erreur')
        return redirect(url_for('animal'))

    nom = request.form.get('nom')
    race = request.form.get('race')
    enclot = request.form.get('enclot')
    arrive = request.form.get('arrive')
    depart = request.form.get('depart')
    enclot = request.form.get('enclot')
    zone = request.form.get('zone')

    if nom:
        animal.nom = nom
    if race:
        animal.espèce = race
    if enclot:
        animal.enclot = enclot
    if arrive:
        animal.arrive = arrive
    if depart != "":
        animal.depart = depart or None
    if enclot:
        animal.enclot = enclot
    if zone:
        animal.zone = zone

    db.session.commit()
    flash("Animal modifié avec succès.", 'success')

    return redirect(url_for('animal'))
    
@app.route("/api/events")
def get_events():
    events = Event.query.all()
    result = [
        {
            "id": e.id,
            "title": e.title,
            "start": e.start,
            "end": e.end
        }
        for e in events
    ]
    return jsonify(result)

@app.route('/addevent', methods=['GET', 'POST'])
@login_required
def addevent():
    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à ajouter des événements.", 'danger')
        return redirect(url_for('acceuil'))

    if request.method == 'POST':
        title = request.form.get('title')
        start = request.form.get('start')
        end = request.form.get('end')

        if not title or not start or not end:
            flash('Tous les champs sont requis.', 'danger')
            return redirect(url_for('addevent'))

        new_event = Event(title=title, start=start, end=end)
        db.session.add(new_event)
        db.session.commit()
        flash('Événement ajouté avec succès.', 'success')
        return redirect(url_for('addevent'))

    return render_template('addevents.html')

@app.route('/deletevents', methods=['POST', 'GET'])
@login_required
def deletevents():
    if request.method == 'GET':
        flash('Méthode non autorisée.', 'danger')
        return redirect(url_for('addevent'))

    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à supprimer des événements.", 'danger')
        return redirect(url_for('addevent'))
    
    event_ids = request.form.getlist('event_ids')
    if event_ids:
        for event_id in event_ids:
            event = Event.query.get(int(event_id))
            if event:
                db.session.delete(event)
        db.session.commit()
        flash(f'{len(event_ids)} événement(s) supprimé(s) avec succès.', 'success')
    else:
        flash('Aucun événement sélectionné.', 'warning')
    return redirect(url_for('addevent'))

@app.route("/api/newtickets", methods=['POST', 'GET'])
@login_required
def new_tickets():
    if request.method == 'POST':
        nom = request.form['nom']
        prénom = request.form['prenom']
        categorie = request.form['categorie']
        date = request.form['date']

        uuid_str = str(uuid.uuid4())

        nouveau_ticket = Tickets(
            nom=nom,
            prenom=prénom,
            uuid=uuid_str,
            validite="True",
            date_visite=date,
            categorie=categorie,
            user_id=current_user.id
        )
        db.session.add(nouveau_ticket)
        db.session.commit()
        flash("Ticket créé avec succès.", 'success')
        return redirect(url_for('compte'))
    
    return render_template(url_for('compte'))

@app.route("/events")
def evenement():
    return render_template("evenement.html")

@app.route("/soins")
@login_required
def soins():
    if current_user.role not in ['soigneur', 'admin']:
        flash("Vous n'avez pas les permissions pour accéder a cette page", 'danger')
        return redirect(url_for('acceuil'))

    soins = Soin.query.all()
    animaux = Animal.query.all()
    soigneurs = Soigneur.query.all()
    return render_template("soins.html", soins=soins, animaux=animaux, soigneurs=soigneurs, datetime=datetime)

@app.route("/api/addsoins", methods=['POST', 'GET'])
@login_required
def add_soins():
    if request.method == 'GET':
        flash('Méthode non autorisée.', 'danger')
        return redirect(url_for('soins'))

    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à ajouter des soins.", 'danger')
        return redirect(url_for('soins'))

    description = request.form['description']
    categorie = request.form['categorie']
    date_str = request.form['date']
    animal_id = request.form['animal_id']
    soigneur_id = request.form['soigneur_id']

    date = datetime.strptime(date_str, "%Y-%m-%d").date()

    nouvel_soin = Soin(
        description=description,
        categorie=categorie,
        date=date,
        animal_id=animal_id,
        soigneur_id=soigneur_id
    )
    db.session.add(nouvel_soin)
    db.session.commit()
    flash("Soin ajouté avec succès.", 'success')

    return redirect(url_for('soins'))

@app.route('/api/editsoins/<int:soin_id>', methods=['POST'])
@login_required
def edit_soins(soin_id):

    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à modifier un soin.", "danger")
        return redirect(url_for('soins'))

    soin = db.session.get(Soin, soin_id)

    if not soin:
        flash("Soin introuvable.", "danger")
        return redirect(url_for('soins'))

    # Récupère les champs du formulaire
    categorie = request.form.get('categorie')
    description = request.form.get('description')
    date_str = request.form.get('date')

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        flash("Date invalide.", "danger")
        return redirect(url_for('soins'))

    # Mise à jour
    soin.categorie = categorie
    soin.description = description
    soin.date = date

    db.session.commit()

    flash("Soin modifié avec succès.", "success")
    return redirect(url_for('soins'))

@app.route('/api/deletesoins/<int:soin_id>', methods=['POST'])
@login_required
def delete_soins(soin_id):

    if current_user.role not in ['admin', 'soigneur']:
        flash("Vous n'êtes pas autorisé à supprimer un soin.", "danger")
        return redirect(url_for('soins'))

    soin = db.session.get(Soin, soin_id)

    if not soin:
        flash("Soin introuvable.", "danger")
        return redirect(url_for('soins'))

    db.session.delete(soin)
    db.session.commit()

    flash("Soin supprimé avec succès.", "success")
    return redirect(url_for('soins'))

@app.route('/map')
def map():
    return render_template('map.html')

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.errorhandler(404)
def page_not_found(e):
    flash("La page que vous recherchez n'existe pas.", 'erreur')
    return render_template("404.html")

# Création des tables de la base de donnee
with app.app_context():
    db.create_all()  # Crée les tables si elles n'existent pas

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
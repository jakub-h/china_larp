from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from citizen import Citizen, CitizenManager
from functools import wraps
import utils
import logging
from logging import FileHandler


class DebugFileHandler(FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        FileHandler.__init__(self, filename, mode, encoding, delay)

    def emit(self, record):
        if not record.levelno == logging.DEBUG:
            return
        FileHandler.emit(self, record)

# set up logging to file - see previous section for more details
logging.basicConfig(filename="debug.log",
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s : %(message)s',
                    datefmt='%m-%d %H:%M:%S',)
# add the handler to the root logger
logging.getLogger('app-logger').addHandler(DebugFileHandler("debug.log"))

app = Flask(__name__)
main_db = "static/db.json"
daily_updates = "static/daily-updates.json"
hackers_db = "static/hackers.json"
day = 0

# Check if logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Pokus o narušení systému!", 'danger')
            return redirect(url_for('login'))
    return wrap

# Check if admin
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and 'admin' in session:
            return f(*args, **kwargs)
        else:
            flash("Pokus of narušení systému!", 'danger')
            return redirect(url_for('home'))
    return wrap

# Register form
class RegisterForm(Form):
    name = StringField('Jméno', [
        validators.InputRequired(),
        validators.Length(min=2, max=30),
    ])
    password = PasswordField('Heslo', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Hesla se neshodují!')
    ])
    confirm = PasswordField('Potvrď heslo', [
        validators.EqualTo('password', message='Hesla se neshodují!')
    ])

# Home
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', day=day)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate():
            name = form.name.data
            password = form.password.data
            # Save to DB
            manager = CitizenManager(main_db)
            user = Citizen(name, password)
            if manager.persist(user):
                flash('Registrace proběhla úspěšně, nyní se prosím přihlašte.', 'success')
                return redirect(url_for('login'))
            else:
                error = 'Uživatel s tímto jménem již existuje.'
                return render_template('register.html', error=error, form=form)
        else:
            error = "Registrace se nezdařila"
            return render_template('register.html', error=error, form=form)
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password_candidate = request.form['password']
        
        user = utils.getActualVersion(name, main_db, daily_updates)
        if user:
            password = user.password
            if password == password_candidate:
                session["logged_in"] = True
                session["name"] = user.name
                # Check admin
                if "admin" in name:
                    session["admin"] = True
                flash("Nyní jsi přihlášen", "success")
                return redirect(url_for('home'))
            else:
                error = 'Nesprávné heslo'
                return render_template('login.html', error=error)
        else:
            error = 'Uživatel nenalezen'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Nyní jsi odhlášen", "success")
    return redirect(url_for('login'))

# Citizens summary
@app.route('/summary')
@is_logged_in
def summary():
    manager = CitizenManager(main_db)
    user = manager.getByName(session['name'])
    citizens = manager.getAll()
    return render_template('summary.html', user=user, citizens=citizens)

# Show rules
@app.route('/rules')
def rules():
    return render_template("rules.html")

# Edit citizen
@app.route('/edit/<string:name>/', methods=['GET', 'POST'])
@is_admin
def edit(name):
    if request.method == "POST":
        if 'interaction' in request.form:
            utils.socailInteraction(name, request.form['interaction_with'], main_db, daily_updates)
            flash("Socialni interakce s: '" + request.form['interaction_with'] + "'. Změna skóre se projeví příští den.", "warning")
            logging.debug("Sociální interakce: {} ({}) s {} ({}) [zadal: {}]".format(
                name,
                utils.getMorningLevel(name, main_db),
                request.form['interaction_with'],
                utils.getMorningLevel(request.form['interaction_with'], main_db),
                session["name"]))
        if 'score_update' in request.form:
            if request.form['score_update'] == "up":
                utils.addScore(name, int(request.form['score_update_value']), main_db, daily_updates)
                flash("Update skore: +" + request.form['score_update_value'] + ". Změna skóre se projeví příští den.", "warning")
                logging.debug("Změna bodů ({}): +{} [zadal: {}]".format(name, request.form['score_update_value'], session['name']))
            if request.form['score_update'] == "down":
                utils.addScore(name, -int(request.form['score_update_value']), main_db, daily_updates)
                flash("Update skore: -" + request.form['score_update_value'] + ". Změna skóre se projeví příští den.", "warning")
                logging.debug("Změna bodů ({}): -{} [zadal: {}]".format(name, request.form['score_update_value'], session['name']))
    manager = CitizenManager(main_db)
    citizen = manager.getByName(name)
    citizens = manager.getAll()
    if citizen:
        return render_template('edit.html', citizen=citizen, citizens=citizens)
    else:
        flash("Uživatel '" + name + "' není v databázi.", "danger")
        return redirect(url_for('summary'))

# Uprate
@app.route('/uprate/<string:name>/')
@is_logged_in
def uprate(name):
    if utils.rate(session['name'], name, 'up', main_db, daily_updates):
        flash('Děkujeme za hodnocení.', 'success')
        logging.debug("Hodnocení (+): {} --> {}".format(session['name'], name))
    else:
        flash('Dnes jsi již využil všechny své možnosti hodnotit.', 'danger')
    return redirect(url_for('summary'))

# Downrate
@app.route('/downrate/<string:name>/')
@is_logged_in
def downrate(name):
    if utils.rate(session['name'], name, 'down', main_db, daily_updates):
        flash('Děkujeme za hodnocení.', 'success')
        logging.debug("Hodnocení (-): {} --> {}".format(session['name'], name))
    else:
        flash('Dnes jsi již využil všechny své možnosti hodnotit.', 'danger')
    return redirect(url_for('summary'))

# Actions
@app.route('/actions/<string:action>', methods=['GET', 'POST'])
@is_logged_in
def actions(action):
    if action in ["food", "pub", "school", "volunteer", "parents", "beauty"]:
        utils.processAction(session['name'], action, main_db, daily_updates)
        return render_template("universal.html", day=day)
    if action == "internet":
        if request.method == 'POST':
            if "camouflage" in request.form:
                utils.addScore(session['name'], -3, main_db, daily_updates)
                flash("Spustil jsi hru nebo video na internetu.", "info")
                return render_template("internet.html")
            if "hacking" in request.form:
                if request.form['hacked-password'] == "hongkongjesoucastciny":
                    utils.addScore(session['name'], 25, main_db, daily_updates)
                    flash("Podařilo se ti prolomit do systému a upravit si svůj bodový účet.\
                           Ale jen lehce, aby nikdo nepojal podezření.", "success")
                    logging.debug("Hacker (úspěch): {}".format(session['name']))
                    hackers_manager = CitizenManager(hackers_db)
                    citizen = utils.getActualVersion(session['name'], main_db, daily_updates)
                    hackers_manager.persist(citizen)
                    return redirect(url_for('home'))
                else:
                    flash("Toto není správné heslo!", "danger")
                    logging.debug("Hacker (neúspěch): {} (pokus: {})"
                        .format(session['name'], request.form['hacked-password']))
                    return render_template("internet.html")
        hackers_manager = CitizenManager(hackers_db)
        citizen = hackers_manager.getByName(session['name'])
        if citizen:
            already_hacked = True
        else:
            already_hacked = False
        return render_template("internet.html", already_hacked=already_hacked)

# Remove citizen
@app.route('/remove/<string:name>/')
@is_admin
def remove(name):
    manager = CitizenManager(main_db)
    manager.removeByName(name)
    flash("Uživatel '" + name + "' úspěšně vymazán.", "success")
    return redirect(url_for('home'))

# End the day
@app.route('/end_day')
@is_admin
def end_day():
    daily_manager = CitizenManager(daily_updates)
    updates = daily_manager.getAll()
    daily_manager.clearDb()
    manager = CitizenManager(main_db)
    for citizen in updates:
        citizen.num_of_ratings = 0
        manager.update(citizen)
    global day
    day += 1
    logging.debug("Konec dne ({}.1. -> {}.1.) [zadal: {}]".format(10+day, 11+day, session['name']))
    return redirect(url_for('home'))

# Main   
if __name__ == '__main__':
    app.secret_key = 'velmibezpecnyatajnyklic'
    app.run(host='0.0.0.0', port=5000, debug=True)

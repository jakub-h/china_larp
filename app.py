from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from citizen import Citizen, CitizenManager
from functools import wraps

app = Flask(__name__)
main_db = "static/db.json"
daily_updates = "static/daily-updates.json"

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
        validators.DataRequired(),
        validators.Length(min=2, max=30),
        validators.NoneOf(["admin"])
    ])
    password = PasswordField('Heslo', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Hesla se neshodují!')
    ])
    confirm = PasswordField('Potvrď heslo', [
        validators.EqualTo('password', message='Hesla se neshodují!')
    ])

# Home
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

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
        
        manager = CitizenManager(main_db)
        user = manager.getByName(name)
        if user:
            password = user.password
            if password == password_candidate:
                session["logged_in"] = True
                session["name"] = user.name
                session["level"] = user.getLevel()
                # Check num of ratings done today
                manager = CitizenManager(daily_updates)
                updates = manager.getByName(name)
                if updates:
                    session["num_of_ratings"] = updates.num_of_ratings
                else:
                    session["num_of_ratings"] = 0
                # Check admin
                if name == "admin":
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
def summary():
    manager = CitizenManager(main_db)
    citizens = manager.getAll()
    return render_template('summary.html', citizens=citizens)

# Edit citizen
@app.route('/edit/<string:name>/', methods=['GET', 'POST'])
@is_admin
def edit(name):
    if request.method == "POST":
        if 'interaction' in request.form:
            # TODO Socialni interakce
            flash("Socialni interakce s: '" + request.form['interaction_with'] + "'", "warning")
        if 'score_update' in request.form:
            if request.form['score_update'] == "up":
                # TODO Pridat body
                flash("Update skore: +" + request.form['score_update_value'], "warning")
            if request.form['score_update'] == "down":
                # TODO Odebrat body
                flash("Update skore: -" + request.form['score_update_value'], "warning")
    manager = CitizenManager(main_db)
    citizen = manager.getByName(name)
    citizens = manager.getAll()
    if citizen:
        return render_template('edit.html', citizen=citizen, citizens=citizens)
    else:
        flash("Uživatel '" + name + "' není v databázi.", "danger")
        return redirect(url_for('summary'))

# Remove citizen
@app.route('/remove/<string:name>/')
@is_admin
def remove(name):
    manager = CitizenManager(main_db)
    if manager.removeByName(name):
        flash("Uživatel '" + name + "' úspěšně vymazán.", "success")
    else:
        flash("Něco se pokazilo při mazání uživatele '" + name + "'. Nejspíš nebyl v databázi.", "danger")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.secret_key = 'velmibezpecnyatajnyklic'
    app.run(host='0.0.0.0', debug=True)

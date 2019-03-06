from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from citizen import Citizen, CitizenManager
from functools import wraps

app = Flask(__name__)
db_filename = "static/db.json"

# Home
@app.route('/')
def home():
    return render_template('home.html')

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

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate():
            name = form.name.data
            password = form.password.data
            # Save to DB
            manager = CitizenManager(db_filename)
            citizen = Citizen(name, password)
            manager.persist(citizen)
            # Message and redirect
            flash('Registrace proběhla úspěšně, nyní se prosím přihlašte.', 'success')
            return redirect(url_for('login'))
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
        
        manager = CitizenManager(db_filename)
        citizen = manager.getByName(name)
        if citizen:
            password = citizen.password
            if password == password_candidate:
                app.logger.info("LOGIN: password matched")
                session["logged_in"] = True
                session["name"] = name
                flash("Nyní jsi přihlášn", "success")
                return redirect(url_for('dashboard'))
            else:
                error = 'Nesprávné heslo'
                app.logger.info("LOGIN: password did not match")
                return render_template('login.html', error=error)
        else:
            error = 'Uživatel nenalezen'
            app.logger.info("LOGIN: no user with name: '" + name + "' found")
            return render_template('login.html', error=error)


    return render_template('login.html')

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


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Nyní jsi odhlášen", "success")
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.secret_key = 'verysecretkey1234'
    app.run(host='0.0.0.0', debug=True)

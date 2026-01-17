"""Flask web app for a LARP inspired by the Chinese social credit system."""

from __future__ import annotations

import io
import logging
from collections.abc import Callable
from functools import wraps
from logging import FileHandler
from typing import Any

import segno
from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import Form, PasswordField, StringField, validators

import utils
from citizen import Citizen, CitizenManager


class DebugFileHandler(FileHandler):
    """A file handler that only persists DEBUG logs."""

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: str | None = None,
        delay: bool = False,
    ) -> None:
        """Create a debug-only file handler."""

        super().__init__(filename, mode, encoding, delay)

    def emit(self, record: logging.LogRecord) -> None:
        """Write a log record to file if it is DEBUG."""

        if record.levelno != logging.DEBUG:
            return
        super().emit(record)


# set up logging to file - see previous section for more details
logging.basicConfig(
    filename="debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s : %(message)s",
    datefmt="%m-%d %H:%M:%S",
)
# add the handler to the root logger
logging.getLogger("app-logger").addHandler(DebugFileHandler("debug.log"))

app = Flask(__name__)

MAIN_DB = "static/db.json"
DAILY_UPDATES_DB = "static/daily-updates.json"
HACKERS_DB = "static/hackers.json"
DAY_CONFIG_KEY = "DAY"
app.config.setdefault(DAY_CONFIG_KEY, 0)


def get_day() -> int:
    """Return the current in-memory game day counter."""

    return int(app.config.get(DAY_CONFIG_KEY, 0))


def increment_day() -> int:
    """Increment the in-memory game day counter and return the new value."""

    new_day = get_day() + 1
    app.config[DAY_CONFIG_KEY] = new_day
    return new_day


SESSION_LOGGED_IN = "logged_in"
SESSION_NAME = "name"
SESSION_ADMIN = "admin"


# Check if logged in
def is_logged_in(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require a logged-in session for a route."""

    @wraps(view)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        if SESSION_LOGGED_IN in session:
            return view(*args, **kwargs)
        flash("Pokus o narušení systému!", "danger")
        return redirect(url_for("login"))

    return wrap


# Check if admin
def is_admin(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require an admin session for a route."""

    @wraps(view)
    def wrap(*args: Any, **kwargs: Any) -> Any:
        if SESSION_LOGGED_IN in session and SESSION_ADMIN in session:
            return view(*args, **kwargs)
        flash("Pokus o narušení systému!", "danger")
        return redirect(url_for("home"))

    return wrap


# Register form
class RegisterForm(Form):
    """WTForms definition for user registration."""

    name = StringField(
        "Jméno",
        [
            validators.InputRequired(),
            validators.Length(min=2, max=30),
        ],
    )
    password = PasswordField(
        "Heslo",
        [
            validators.InputRequired(),
            validators.EqualTo("confirm", message="Hesla se neshodují!"),
        ],
    )
    confirm = PasswordField(
        "Potvrď heslo", [validators.EqualTo("password", message="Hesla se neshodují!")]
    )


# Home
@app.route("/")
@app.route("/home")
def home() -> str:
    """Render the home page."""

    public_base_url = utils.get_public_base_url(request)
    return render_template("home.html", day=get_day(), public_base_url=public_base_url)


@app.route("/health")
def health() -> dict[str, str]:
    """Health-check endpoint."""

    return {"status": "ok"}


@app.route("/qr.svg")
def qr_svg() -> Response:
    """Return an SVG QR code for the public base URL."""

    url = utils.get_public_base_url(request)
    qr = segno.make(url)
    buff = io.BytesIO()
    qr.save(buff, kind="svg", scale=6, border=1, xmldecl=False)
    return Response(buff.getvalue(), mimetype="image/svg+xml")


# Register
@app.route("/register", methods=["GET", "POST"])
def register() -> ResponseReturnValue:
    """Register a new user account."""

    form = RegisterForm(request.form)
    if request.method == "POST":
        if form.validate():
            name = str(form.name.data).strip()
            password = str(form.password.data)
            # Save to DB
            manager = CitizenManager(MAIN_DB)
            user = Citizen(name, generate_password_hash(password))
            if manager.persist(user):
                flash(
                    "Registrace proběhla úspěšně, nyní se prosím přihlašte.", "success"
                )
                return redirect(url_for("login"))
            error = "Uživatel s tímto jménem již existuje."
            return render_template("register.html", error=error, form=form)
        error = "Registrace se nezdařila"
        return render_template("register.html", error=error, form=form)
    return render_template("register.html", form=form)


# Login
@app.route("/login", methods=["GET", "POST"])
def login() -> ResponseReturnValue:
    """Log in a user and create a session."""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password_candidate = request.form.get("password", "")
        if not name:
            return render_template("login.html", error="Zadej prosím jméno.")

        user = utils.get_actual_version(name, MAIN_DB, DAILY_UPDATES_DB)
        if user is not None:
            password_ok = False
            used_plaintext_fallback = False
            try:
                password_ok = check_password_hash(user.password, password_candidate)
            except (TypeError, ValueError):
                used_plaintext_fallback = True
                password_ok = user.password == password_candidate

            if password_ok:
                # If the record was legacy plaintext, upgrade it in the main DB.
                if used_plaintext_fallback:
                    main_manager = CitizenManager(MAIN_DB)
                    main_user = main_manager.get_by_name(name)
                    if main_user is not None:
                        main_user.password = generate_password_hash(password_candidate)
                        main_manager.update(main_user)

                session[SESSION_LOGGED_IN] = True
                session[SESSION_NAME] = user.name
                # Check admin
                if name.startswith("admin_"):
                    session[SESSION_ADMIN] = True
                flash("Nyní jsi přihlášen", "success")
                return redirect(url_for("home"))
            error = "Nesprávné heslo"
            return render_template("login.html", error=error)
        error = "Uživatel nenalezen"
        return render_template("login.html", error=error)
    return render_template("login.html")


# Logout
@app.route("/logout")
def logout() -> ResponseReturnValue:
    """Log out the current user."""

    session.clear()
    flash("Nyní jsi odhlášen", "success")
    return redirect(url_for("login"))


# Citizens summary
@app.route("/summary")
@is_logged_in
def summary() -> str:
    """Show the current user and the citizen leaderboard."""

    manager = CitizenManager(MAIN_DB)
    user_name = str(session.get(SESSION_NAME, ""))
    user = manager.get_by_name(user_name)
    citizens = manager.get_all()
    return render_template("summary.html", user=user, citizens=citizens)


# Show rules
@app.route("/rules")
def rules() -> str:
    """Show game rules."""

    return render_template("rules.html")


# Edit citizen
@app.route("/edit/<string:name>/", methods=["GET", "POST"])
@is_admin
def edit(name: str) -> ResponseReturnValue:
    """
    Admin view to edit a citizen: interactions and score changes.

    Parameters
    ----------
    name
        Citizen name to edit.
    """

    def _parse_int(value: str, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    if request.method == "POST":
        if "interaction" in request.form:
            interaction_with = request.form.get("interaction_with", "").strip()
            if interaction_with:
                utils.social_interaction(
                    name, interaction_with, MAIN_DB, DAILY_UPDATES_DB
                )
            flash(
                "Socialni interakce s: '"
                + request.form.get("interaction_with", "")
                + "'. Změna skóre se projeví příští den.",
                "warning",
            )
            logging.debug(
                "Sociální interakce: %s (%s) s %s (%s) [zadal: %s]",
                name,
                utils.get_morning_level(name, MAIN_DB),
                interaction_with,
                utils.get_morning_level(interaction_with, MAIN_DB),
                session.get(SESSION_NAME, ""),
            )
        if "score_update" in request.form:
            if request.form["score_update"] == "up":
                delta = _parse_int(request.form.get("score_update_value", "0"))
                utils.add_score(name, delta, MAIN_DB, DAILY_UPDATES_DB)
                flash(
                    "Update skore: +"
                    + request.form.get("score_update_value", "0")
                    + ". Změna skóre se projeví příští den.",
                    "warning",
                )
                logging.debug(
                    "Změna bodů (%s): +%s [zadal: %s]",
                    name,
                    request.form.get("score_update_value", "0"),
                    session.get(SESSION_NAME, ""),
                )
            if request.form["score_update"] == "down":
                delta = _parse_int(request.form.get("score_update_value", "0"))
                utils.add_score(name, -delta, MAIN_DB, DAILY_UPDATES_DB)
                flash(
                    "Update skore: -"
                    + request.form.get("score_update_value", "0")
                    + ". Změna skóre se projeví příští den.",
                    "warning",
                )
                logging.debug(
                    "Změna bodů (%s): -%s [zadal: %s]",
                    name,
                    request.form.get("score_update_value", "0"),
                    session.get(SESSION_NAME, ""),
                )
    manager = CitizenManager(MAIN_DB)
    citizen = manager.get_by_name(name)
    citizens = manager.get_all()
    if citizen is not None:
        return render_template("edit.html", citizen=citizen, citizens=citizens)
    flash("Uživatel '" + name + "' není v databázi.", "danger")
    return redirect(url_for("summary"))


# Uprate
@app.route("/uprate/<string:name>/")
@is_logged_in
def uprate(name: str) -> ResponseReturnValue:
    """
    Apply an up-rating from the current user to the given citizen.

    Parameters
    ----------
    name
        The rated citizen name.
    """

    if utils.rate(
        str(session.get(SESSION_NAME, "")), name, "up", MAIN_DB, DAILY_UPDATES_DB
    ):
        flash("Děkujeme za hodnocení.", "success")
        logging.debug("Hodnocení (+): %s --> %s", session.get(SESSION_NAME, ""), name)
    else:
        flash("Dnes jsi již využil všechny své možnosti hodnotit.", "danger")
    return redirect(url_for("summary"))


# Downrate
@app.route("/downrate/<string:name>/")
@is_logged_in
def downrate(name: str) -> ResponseReturnValue:
    """
    Apply a down-rating from the current user to the given citizen.

    Parameters
    ----------
    name
        The rated citizen name.
    """

    if utils.rate(
        str(session.get(SESSION_NAME, "")), name, "down", MAIN_DB, DAILY_UPDATES_DB
    ):
        flash("Děkujeme za hodnocení.", "success")
        logging.debug("Hodnocení (-): %s --> %s", session.get(SESSION_NAME, ""), name)
    else:
        flash("Dnes jsi již využil všechny své možnosti hodnotit.", "danger")
    return redirect(url_for("summary"))


# Actions
@app.route("/actions/<string:action>", methods=["GET", "POST"])
@is_logged_in
def actions(action: str) -> ResponseReturnValue:
    """
    Handle an action for the current user.

    Parameters
    ----------
    action
        Action key (e.g. ``food``, ``internet``).
    """

    if action in ["food", "pub", "school", "volunteer", "parents", "beauty"]:
        utils.process_action(
            str(session.get(SESSION_NAME, "")), action, MAIN_DB, DAILY_UPDATES_DB
        )
        return render_template("universal.html", day=get_day())
    if action == "internet":
        if request.method == "POST":
            if "camouflage" in request.form:
                utils.add_score(
                    str(session.get(SESSION_NAME, "")), -3, MAIN_DB, DAILY_UPDATES_DB
                )
                flash("Spustil jsi hru nebo video na internetu.", "info")
                return render_template("internet.html")
            if "hacking" in request.form:
                hacked_password = request.form.get("hacked-password", "")
                if hacked_password == "hongkongjesoucastciny":
                    utils.add_score(
                        str(session.get(SESSION_NAME, "")),
                        25,
                        MAIN_DB,
                        DAILY_UPDATES_DB,
                    )
                    flash(
                        (
                            "Podařilo se ti prolomit do systému a upravit si svůj "
                            "bodový účet. "
                            "Ale jen lehce, aby nikdo nepojal podezření."
                        ),
                        "success",
                    )
                    logging.debug("Hacker (úspěch): %s", session.get(SESSION_NAME, ""))
                    hackers_manager = CitizenManager(HACKERS_DB)
                    citizen = utils.get_actual_version(
                        str(session.get(SESSION_NAME, "")), MAIN_DB, DAILY_UPDATES_DB
                    )
                    if citizen is not None:
                        hackers_manager.persist(citizen)
                    return redirect(url_for("home"))
                flash("Toto není správné heslo!", "danger")
                logging.debug(
                    "Hacker (neúspěch): %s (pokus: %s)",
                    session.get(SESSION_NAME, ""),
                    request.form.get("hacked-password", ""),
                )
                return render_template("internet.html")
        hackers_manager = CitizenManager(HACKERS_DB)
        citizen = hackers_manager.get_by_name(str(session.get(SESSION_NAME, "")))
        already_hacked = citizen is not None
        return render_template("internet.html", already_hacked=already_hacked)
    return abort(404)


# Remove citizen
@app.route("/remove/<string:name>/")
@is_admin
def remove(name: str) -> ResponseReturnValue:
    """
    Remove a citizen from the main database.

    Parameters
    ----------
    name
        Citizen name to remove.
    """

    manager = CitizenManager(MAIN_DB)
    manager.remove_by_name(name)
    flash("Uživatel '" + name + "' úspěšně vymazán.", "success")
    return redirect(url_for("home"))


# End the day
@app.route("/end_day")
@is_admin
def end_day() -> ResponseReturnValue:
    """Apply daily updates and reset per-day counters."""

    daily_manager = CitizenManager(DAILY_UPDATES_DB)
    updates = daily_manager.get_all()
    daily_manager.clear_db()
    manager = CitizenManager(MAIN_DB)
    for citizen in updates:
        citizen.num_of_ratings = 0
        manager.update(citizen)
    day = increment_day()
    logging.debug(
        "Konec dne (%s.1. -> %s.1.) [zadal: %s]",
        10 + day,
        11 + day,
        session.get(SESSION_NAME, ""),
    )
    return redirect(url_for("home"))


# Main
if __name__ == "__main__":
    # For production, set SECRET_KEY env var; fallback is fine for local LARP use.
    app.secret_key = utils.get_secret_key()
    app.run(
        host=utils.get_bind_host(),
        port=utils.get_bind_port(),
        debug=utils.get_debug(),
    )

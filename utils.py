"""Helper functions for the game logic and Flask runtime configuration."""

from __future__ import annotations

import os
import secrets

from flask import Request, flash

from citizen import Citizen, CitizenManager


def get_actual_version(name: str, main_db: str, daily_updates: str) -> Citizen | None:
    """
    Return a citizen state, preferring today's updates.

    Parameters
    ----------
    name
        Citizen name to load.
    main_db
        Path to the main TinyDB JSON.
    daily_updates
        Path to the "today changes" TinyDB JSON.

    Returns
    -------
    Citizen or None
        Citizen if found, else None.
    """

    daily_manager = CitizenManager(daily_updates)
    updates = daily_manager.get_by_name(name)
    if updates is not None:
        return updates

    manager = CitizenManager(main_db)
    return manager.get_by_name(name)


def get_morning_level(name: str, main_db: str) -> int:
    """
    Return the citizen level from the main DB (ignores today's updates).

    Parameters
    ----------
    name
        Citizen name.
    main_db
        Path to the main TinyDB JSON.

    Returns
    -------
    int
        The citizen level (1..7).
    """

    manager = CitizenManager(main_db)
    citizen = manager.get_by_name(name)
    if citizen is None:
        # Keep legacy behavior roughly intact: unknown user acts as "worst" level.
        return 7
    return citizen.get_level()


def social_interaction(
    name_a: str, name_b: str, main_db: str, daily_updates: str
) -> None:
    """
    Apply a social interaction update between two citizens.

    The delta depends on the *morning* levels (i.e., ignoring today's changes).
    The update itself is stored into the daily updates DB.

    Parameters
    ----------
    name_a
        First citizen name.
    name_b
        Second citizen name.
    main_db
        Path to the main TinyDB JSON.
    daily_updates
        Path to the "today changes" TinyDB JSON.
    """

    # Get current level not affected by today's changes
    citizen_a_level = get_morning_level(name_a, main_db)
    citizen_b_level = get_morning_level(name_b, main_db)
    citizen_a = get_actual_version(name_a, main_db, daily_updates)
    citizen_b = get_actual_version(name_b, main_db, daily_updates)
    if citizen_a is None or citizen_b is None:
        return

    update = abs(citizen_a_level - citizen_b_level) * 2

    # Lower level has interaction with higher level -> lower level gains points
    # and higher level lose points.
    citizen_a.score += update if citizen_a_level > citizen_b_level else -update
    citizen_b.score += update if citizen_b_level > citizen_a_level else -update

    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen_a)
    daily_manager.update(citizen_b)


def add_score(name: str, value: int, main_db: str, daily_updates: str) -> None:
    """
    Add a score delta and persist it into daily updates.

    Parameters
    ----------
    name
        Citizen name.
    value
        Score delta (can be negative).
    main_db
        Path to the main TinyDB JSON.
    daily_updates
        Path to the "today changes" TinyDB JSON.
    """

    citizen = get_actual_version(name, main_db, daily_updates)
    if citizen is None:
        return
    citizen.score += value

    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen)


def rate(
    rating_name: str,
    rated_name: str,
    direction: str,
    main_db: str,
    daily_updates: str,
) -> bool:
    """
    Apply a rating action (up/down) and persist daily updates.

    Parameters
    ----------
    rating_name
        The citizen giving the rating.
    rated_name
        The citizen being rated.
    direction
        Either ``"up"`` or ``"down"``.
    main_db
        Path to the main TinyDB JSON.
    daily_updates
        Path to the "today changes" TinyDB JSON.

    Returns
    -------
    bool
        True if rating was applied; False if daily limit was reached.
    """

    rating = get_actual_version(rating_name, main_db, daily_updates)
    rated = get_actual_version(rated_name, main_db, daily_updates)
    if rating is None or rated is None:
        return False

    if rating.num_of_ratings < 3:
        if direction == "down":
            rating_level = get_morning_level(rating_name, main_db)
            if rating_level < 3:
                rated.score -= 7
            elif rating_level < 6:
                rated.score -= 5
            else:
                rated.score -= 3
            rating.score += 3
        elif direction == "up":
            rated_level = get_morning_level(rated_name, main_db)
            if rated_level < 3:
                rated.score += 3
            elif rated_level < 6:
                rated.score += 2
            else:
                rating.score -= 1
        rating.num_of_ratings += 1
        daily_manager = CitizenManager(daily_updates)
        daily_manager.update(rating)
        daily_manager.update(rated)
        return True
    return False


def process_action(name: str, action: str, main_db: str, daily_updates: str) -> None:
    """
    Apply a named action to a citizen and persist daily updates.

    Parameters
    ----------
    name
        Citizen name.
    action
        Action key (e.g. ``"food"``, ``"pub"``, ``"school"``).
    main_db
        Path to the main TinyDB JSON.
    daily_updates
        Path to the "today changes" TinyDB JSON.
    """

    citizen = get_actual_version(name, main_db, daily_updates)
    if citizen is None:
        return
    if action == "food":
        citizen.score -= 20
        flash("Dnes jsi nesnědl jídlo", "info")
    elif action == "pub":
        citizen.score -= 3
        flash("Dnes jsi navštívil hospodu", "info")
    elif action == "school":
        if citizen.education < 2:
            citizen.education += 1
            flash(
                (
                    f"Získal jsi {citizen.education}. stupeň vzdělání. "
                    "Změna se projeví zítra."
                ),
                "info",
            )
        else:
            flash("Nemůžeš překročit maximální možnou úroveň vzdělání (2).", "danger")
    elif action == "volunteer":
        citizen.score += 5
        flash(
            "Čínská lidová republika ti děkujě za tvou dobrovolnickou činnost.", "info"
        )
    elif action == "parents":
        citizen.score += 4
        flash("Věnoval jsi čas svým starým rodičům.", "info")
    elif action == "beauty":
        citizen.score += 7
        flash("Navštívil jsi salon krásy.", "info")
    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen)


def get_secret_key() -> str:
    """
    Return a Flask secret key.

    Prefer the SECRET_KEY environment variable; otherwise generate a random key
    for local development runs.
    """
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    return secrets.token_hex(32)


def get_public_base_url(request: Request) -> str:
    """
    Return the URL players should use to access the game.

    If PUBLIC_BASE_URL is set (e.g. "http://china.larp/"), it is used.
    Otherwise, the current request host URL is used.
    """
    public_base_url = os.getenv("PUBLIC_BASE_URL")
    if public_base_url:
        if not public_base_url.endswith("/"):
            return public_base_url + "/"
        return public_base_url
    return request.host_url


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_bind_host() -> str:
    """Return the bind host."""
    return os.getenv("HOST", "0.0.0.0")


def get_bind_port() -> int:
    """Return the bind port."""
    try:
        return int(os.getenv("PORT", "5000"))
    except ValueError:
        return 5000


def get_debug() -> bool:
    """Return the debug mode."""
    return _env_bool("DEBUG", False)

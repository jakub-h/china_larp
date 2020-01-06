from citizen import Citizen, CitizenManager
from flask import flash, render_template


def getActualVersion(name, main_db, daily_updates):
    daily_manager = CitizenManager(daily_updates)
    updates = daily_manager.getByName(name)
    if updates:
        return updates
    else:
        manager = CitizenManager(main_db)
        return manager.getByName(name)

def getMorningLevel(name, main_db):
    manager = CitizenManager(main_db)
    citizen = manager.getByName(name)
    return citizen.getLevel()

def socailInteraction(name_a, name_b, main_db, daily_updates):
    # Get current level not affected by todays changes
    citizen_a_level = getMorningLevel(name_a, main_db)
    citizen_b_level = getMorningLevel(name_b, main_db)
    citizen_a = getActualVersion(name_a, main_db, daily_updates)
    citizen_b = getActualVersion(name_b, main_db, daily_updates)

    update = abs(citizen_a_level - citizen_b_level) * 2

    # Lower level has interaction with higher level -> lower level gains points
    # and higher level lose points.
    citizen_a.score += update if citizen_a_level > citizen_b_level else -update
    citizen_b.score += update if citizen_b_level > citizen_a_level else -update

    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen_a)
    daily_manager.update(citizen_b)

def addScore(name, value, main_db, daily_updates):
    citizen = getActualVersion(name, main_db, daily_updates)
    citizen.score += value
    
    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen)

def rate(rating_name, rated_name, direction, main_db, daily_updates):
    rating = getActualVersion(rating_name, main_db, daily_updates)
    rated = getActualVersion(rated_name, main_db, daily_updates)
    if rating.num_of_ratings < 3:
        if direction == "down":
            rating_level = getMorningLevel(rating_name, main_db)
            if rating_level < 3:
                rated.score -= 7
            elif rating_level < 6:
                rated.score -= 5
            else:
                rated.score -= 3
            rating.score += 3
        elif direction == "up":
            rated_level = getMorningLevel(rated_name, main_db)
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

def processAction(name, action, main_db, daily_updates):
    citizen = getActualVersion(name, main_db, daily_updates)
    if action == "food":
        citizen.score -= 20
        flash("Dnes jsi nesnědl jídlo", "info")
    elif action == "pub":
        citizen.score -= 3
        flash("Dnes jsi navštívil hospodu", "info")
    elif action == "school":
        if citizen.education < 2:
            citizen.education += 1
            flash("Získal jsi {}. stupeň vzdělání. Změna se projeví zítra.".format(citizen.education), "info")
        else:
            flash("Nemůžeš překročit maximální možnou úroveň vzdělání (2).", "danger")
    elif action == "volunteer":
        citizen.score += 5
        flash("Čínská lidová republika ti děkujě za tvou dobrovolnickou činnost.", "info")
    elif action == "parents":
        citizen.score += 4
        flash("Věnoval jsi čas svým starým rodičům.", "info")
    elif action == "beauty":
        citizen.score += 7
        flash("Navštívil jsi salon krásy.", "info")
    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(citizen)

    



from citizen import Citizen, CitizenManager


def getActualVersion(name, main_db, daily_updates):
    manager = CitizenManager(daily_updates)
    updates = manager.getByName(name)
    if updates:
        return updates
    else:
        manager = CitizenManager(main_db)
        return manager.getByName(name)

def getMorningLevel(name, main_db):
    manager = CitizenManager(main_db)
    citizen = manager.getByName(name)
    return citizen.getLevel()

def socailInteraction(first_name, second_name, main_db, daily_updates):
    # Get current level not affected by todays changes
    first_level = getMorningLevel(first_name, main_db)
    second_level = getMorningLevel(second_name, main_db)

    first = getActualVersion(first_name, main_db, daily_updates)
    second = getActualVersion(second_name, main_db, daily_updates)
    first.score -= 2 * (first_level - second_level)
    second.score += 2 * (first_level - second_level)

    daily_manager = CitizenManager(daily_updates)
    daily_manager.update(first)
    daily_manager.update(second)

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
            rating.num_of_ratings += 1
        elif direction == "up":
            rated_level = getMorningLevel(rated_name, main_db)
            if rated_level < 3:
                rated.score += 3
            elif rated_level < 6:
                rated.score +=2
            else:
                rating.score -= 1
            rating.num_of_ratings += 1
        manager = CitizenManager(daily_updates)
        manager.update(rating)
        manager.update(rated)
        return True
    return False

def processAction(name, action, main_db, daily_updates):
    citizen = getActualVersion(name, main_db, daily_updates)
    if action == "food":
        citizen.score -= 20
    if action == "pub":
        citizen.score -= 3
    if action == "volunteer":
        citizen.score += 5
    if action == "parents":
        citizen.score += 4
    if action == "beauty":
        citizen.score += 7
    if action == "red":
        citizen.score -= 2
    if action == "internet":
        citizen.score -= 3
    manager = CitizenManager(daily_updates)
    manager.update(citizen)
                
    



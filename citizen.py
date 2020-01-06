from tinydb import TinyDB, Query

class Citizen:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.score = 0
        self.num_of_ratings = 0
        self.education = 0

    def toDict(self):
        return {
            'name':self.name,
            'password':self.password,
            'score':self.score,
            'num_of_ratings':self.num_of_ratings,
            'education':self.education}
        
    def getLevel(self):
        if self.score > 90:
            return 1
        if self.score > 70:
            return 2
        if self.score > 55:
            return 3
        if self.score > 45:
            return 4
        if self.score > 30:
            return 5
        if self.score > 10:
            return 6
        return 7


class CitizenManager:
    def __init__(self, filename):
        self.db_filename = filename

    def constructCitizen(self, name, password, score, num_of_ratings, education):
        citizen = Citizen(name, password)
        citizen.score = score
        citizen.num_of_ratings = num_of_ratings
        citizen.education = education
        return citizen

    def persist(self, citizen):
        db = TinyDB(self.db_filename)
        query = Query()
        if not db.contains(query.name == citizen.name):
            db.insert(citizen.toDict())
            db.close()
            return True
        db.close()
        return False

    def update(self, citizen):
        db = TinyDB(self.db_filename)
        query = Query()
        if citizen.name != None:
            if citizen.score > 100:
                citizen.score = 100
            if citizen.score < 0:
                citizen.score = 0
            # Updated if exists, inserted if not
            db.upsert(citizen.toDict(), query.name == citizen.name)
            db.close()
            return True
        db.close()
        return False
    
    def getAll(self):
        db = TinyDB(self.db_filename)
        db_result = db.all()
        result = []
        for person in db_result:
            if not 'admin' in person['name']:
                result.append(self.constructCitizen(person['name'],
                                                    person['password'],
                                                    person['score'],
                                                    person['num_of_ratings'],
                                                    person['education']))
        db.close()
        return result

    def getByName(self, name):
        db = TinyDB(self.db_filename)
        query = Query()
        db_result = db.search(query.name == name)
        if len(db_result) == 1:
            person = db_result[0]
            citizen = self.constructCitizen(person['name'],
                                            person['password'],
                                            person['score'],
                                            person['num_of_ratings'],
                                            person['education'])
            db.close()
            return citizen
        db.close()
        return None

    def removeByName(self, name):
        db = TinyDB(self.db_filename)
        query = Query()
        db.remove(query.name == name)
        db.close()

    def clearDb(self):
        db = TinyDB(self.db_filename)
        db.purge()
        db.close()
        


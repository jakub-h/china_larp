from tinydb import TinyDB, Query

class Citizen:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.id = None
        self.score = 0

    def toDict(self):
        return {'name':self.name, 'password':self.password, 'score':self.score}

class CitizenManager:
    def __init__(self, filename):
        self.db_filename = filename

    def constructCitizen(self, name, password, score, id):
        citizen = Citizen(name, password)
        citizen.id = id
        citizen.score = score
        return citizen

    def persist(self, citizen):
        db = TinyDB(self.db_filename)
        query = Query()
        if citizen.id == None and not db.contains(query.name == citizen.name):
            citizen.id = db.insert(citizen.toDict())
            db.close()
            return True
        db.close()
        return False

    def update(self, citizen):
        db = TinyDB(self.db_filename)
        if citizen.id != None:
            db.update(citizen.toDict(), doc_id=citizen.id)
            db.close()
            return True
        db.close()
        return False
    
    def getAll(self):
        db = TinyDB(self.db_filename)
        db_result = db.all()
        result = []
        for person in db_result:
            result.append(self.constructCitizen(person['name'], person['password'], person['score'], person.eid))
        db.close()
        return result
    
    def updateScore(self, id, newScore):
        db = TinyDB(self.db_filename)
        if id != None and db.contains(eid=id):
            db.update({"score":newScore}, eid=id)
            db.close()
            return True
        db.close()
        return False

    def getById(self, ids):
        db = TinyDB(self.db_filename)
        if db.contains(eids=ids):
            result = []
            db_result = db.get(eids=ids)
            for person in db_result:
                result.append(self.constructCitizen(person['name'], person['password'], person['score'], person.eid))
            db.close()
            return result
        db.close()
        return None

    def getByName(self, name):
        db = TinyDB(self.db_filename)
        query = Query()
        db_result = db.search(query.name == name)
        if len(db_result) == 1:
            person = db_result[0]
            citizen = self.constructCitizen(person['name'], person['password'], person['score'], person.eid)
            db.close()
            return citizen
        db.close()
        return None

    def removeById(self, id):
        db = TinyDB(self.db_filename)
        db.remove(eid=id)
        db.close()
        

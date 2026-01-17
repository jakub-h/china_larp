"""Citizen domain model and TinyDB-backed persistence."""

from __future__ import annotations

from dataclasses import dataclass

from tinydb import Query, TinyDB


@dataclass(slots=True)
class Citizen:
    """
    A single player/admin account in the game.

    Attributes
    ----------
    name
        Player name (admins are identified by an ``admin_`` prefix).
    password
        Password hash stored in DB (Werkzeug).
        Legacy databases may still contain plaintext until users log in once.
    score
        Social score (0..100).
    num_of_ratings
        Remaining daily rating actions counter (resets each day).
    education
        Education level (0..2).
    """

    name: str
    password: str
    score: int = 0
    num_of_ratings: int = 0
    education: int = 0

    def to_dict(self) -> dict[str, object]:
        """
        Convert the citizen to a TinyDB-storable dictionary.

        Returns
        -------
        dict
            JSON-serializable representation of the citizen.
        """

        return {
            "name": self.name,
            "password": self.password,
            "score": self.score,
            "num_of_ratings": self.num_of_ratings,
            "education": self.education,
        }

    def get_level(self) -> int:
        """
        Return the citizen's level derived from score.

        Returns
        -------
        int
            Level in range 1..7 (lower is better).
        """

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
    """TinyDB-backed storage for :class:`~citizen.Citizen`."""

    def __init__(self, filename: str) -> None:
        """
        Create a manager for a TinyDB JSON file.

        Parameters
        ----------
        filename
            Path to the TinyDB JSON file.
        """

        self.db_filename = filename

    def _construct_citizen_from_record(self, record: dict[str, object]) -> Citizen:
        """Build a citizen from a raw TinyDB record."""

        def _coerce_int(value: object | None, default: int = 0) -> int:
            """Best-effort conversion of TinyDB values to int."""

            if value is None:
                return default
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(value.strip())
                except ValueError:
                    return default
            try:
                return int(str(value))
            except ValueError:
                return default

        name = str(record.get("name", ""))
        password = str(record.get("password", ""))

        score = _coerce_int(record.get("score"), 0)
        num_of_ratings = _coerce_int(record.get("num_of_ratings"), 0)
        education = _coerce_int(record.get("education"), 0)

        return Citizen(
            name=name,
            password=password,
            score=score,
            num_of_ratings=num_of_ratings,
            education=education,
        )

    def persist(self, citizen: Citizen) -> bool:
        """
        Insert a new citizen, if the name doesn't exist.

        Parameters
        ----------
        citizen
            Citizen to insert.

        Returns
        -------
        bool
            True if inserted; False if already exists.
        """

        db = TinyDB(self.db_filename)
        query = Query()
        try:
            if not db.contains(query.name == citizen.name):
                db.insert(citizen.to_dict())
                return True
            return False
        finally:
            db.close()

    def update(self, citizen: Citizen) -> bool:
        """
        Upsert an existing citizen (or insert if missing).

        Parameters
        ----------
        citizen
            Citizen to upsert. The name is used as the primary key.

        Returns
        -------
        bool
            True if the citizen had a non-empty name; otherwise False.
        """

        if not citizen.name:
            return False

        citizen.score = min(max(int(citizen.score), 0), 100)
        citizen.num_of_ratings = max(int(citizen.num_of_ratings), 0)
        citizen.education = min(max(int(citizen.education), 0), 2)

        db = TinyDB(self.db_filename)
        query = Query()
        try:
            db.upsert(citizen.to_dict(), query.name == citizen.name)
            return True
        finally:
            db.close()

    def get_all(self) -> list[Citizen]:
        """Return all non-admin citizens."""

        db = TinyDB(self.db_filename)
        try:
            return [
                self._construct_citizen_from_record(person)
                for person in db.all()
                if "admin" not in str(person.get("name", ""))
            ]
        finally:
            db.close()

    def get_by_name(self, name: str) -> Citizen | None:
        """Return a citizen by name."""

        db = TinyDB(self.db_filename)
        query = Query()
        try:
            db_result = db.search(query.name == name)
            if len(db_result) != 1:
                return None
            return self._construct_citizen_from_record(db_result[0])
        finally:
            db.close()

    def remove_by_name(self, name: str) -> None:
        """Remove a citizen by name."""

        db = TinyDB(self.db_filename)
        query = Query()
        try:
            db.remove(query.name == name)
        finally:
            db.close()

    def clear_db(self) -> None:
        """Remove all rows from the database."""
        db = TinyDB(self.db_filename)
        try:
            # tinydb>=4: purge() was removed; truncate() clears all docs.
            db.truncate()
        finally:
            db.close()

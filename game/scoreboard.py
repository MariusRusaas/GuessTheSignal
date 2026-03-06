"""Scoreboard for tracking player DICE scores per difficulty."""

import json
from typing import Dict, List


class Scoreboard:
    """Tracks player scores per difficulty, persisting in memory for the session."""

    def __init__(self):
        self._scores: Dict[str, List[dict]] = {}

    def add_score(self, difficulty: str, name: str, dice: float):
        """Add a score entry and keep the list sorted by DICE descending."""
        if difficulty not in self._scores:
            self._scores[difficulty] = []
        self._scores[difficulty].append({"name": name, "dice": dice})
        self._scores[difficulty].sort(key=lambda x: x["dice"], reverse=True)

    def get_scores(self, difficulty: str) -> List[dict]:
        """Return list of {name, dice} dicts for a difficulty, best first."""
        return self._scores.get(difficulty, [])

    def has_scores(self) -> bool:
        """Return True if any scores have been recorded this session."""
        return any(bool(v) for v in self._scores.values())

    def save(self, filepath: str) -> bool:
        """Save scoreboard to a JSON file. Returns True on success."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._scores, f, indent=2)
            return True
        except Exception:
            return False

    def load(self, filepath: str) -> bool:
        """Load and merge scoreboard from a JSON file. Returns True on success."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for difficulty, scores in data.items():
                if difficulty not in self._scores:
                    self._scores[difficulty] = []
                self._scores[difficulty].extend(scores)
                self._scores[difficulty].sort(key=lambda x: x["dice"], reverse=True)
            return True
        except Exception:
            return False

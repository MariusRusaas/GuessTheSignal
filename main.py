#!/usr/bin/env python3
"""
GuessTheSignal - A PET Imaging Educational Game

Learn about Positron Emission Tomography (PET) through interactive gameplay.
Use Lines of Response (LOR) and Time-of-Flight (TOF) information to
reconstruct hidden shapes representing medical imaging targets.
"""

from game.game_state import Game


def main():
    """Entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

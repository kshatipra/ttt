from datetime import date
import random

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ttt.schemas.orm import Base, Tournament, Round, Match, Team, Player


@pytest.fixture
def player_names():
    return [
        "Alice", "Bob", "Charlie", "Dana", "Eve", "Frank", "Grace", "Hank",
        "Ivy", "Jack", "Kara", "Leo", "Mona", "Nate", "Olivia", "Pete",
        "Quinn", "Rachel", "Steve", "Tina", "Uma", "Victor", "Wendy", "Xander"
    ]


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:", echo=True)


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    transaction = connection.begin()

    # Bind an individual Session to the connection
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

#
# def test_create_match(db_session):
#     # Create a new match
#     new_match = Match(player0="Alice", player1="Bob", player2="Charlie", player3="Dave", score0=10, score1=15)
#     db_session.add(new_match)
#     db_session.commit()
#
#     # Query the match
#     match = db_session.query(Match).filter_by(player0="Alice").first()
#     assert match is not None
#     assert match.player1 == "Bob"
#     assert match.score0 == 10
#     assert match.score1 == 15
#
#
# def test_create_stats(db_session):
#     # Create a new stats entry
#     new_stats = Stats(path="/path/to/resource", count=5)
#     db_session.add(new_stats)
#     db_session.commit()
#
#     # Query the stats entry
#     stats = db_session.query(Stats).filter_by(path="/path/to/resource").first()
#     assert stats is not None
#     assert stats.count == 5
#
#
# def test_update_match_score(db_session):
#     # Create a new match
#     new_match = Match(player0="Alice", player1="Bob", player2="Charlie", player3="Dave", score0=10, score1=15)
#     db_session.add(new_match)
#     db_session.commit()
#
#     # Update the match score
#     match = db_session.query(Match).filter_by(player0="Alice").first()
#     match.score0 = 20
#     db_session.commit()
#
#     # Query the updated match
#     updated_match = db_session.query(Match).filter_by(player0="Alice").first()
#     assert updated_match.score0 == 20
#
#
# def test_increment_stats_count(db_session):
#     # Create a new stats entry
#     new_stats = Stats(path="/path/to/resource", count=5)
#     db_session.add(new_stats)
#     db_session.commit()
#
#     # Increment the stats count
#     stats = db_session.query(Stats).filter_by(path="/path/to/resource").first()
#     stats.count += 1
#     db_session.commit()
#
#     # Query the updated stats entry
#     updated_stats = db_session.query(Stats).filter_by(path="/path/to/resource").first()
#     assert updated_stats.count == 6


def test_create_tournament(db_session):
    tournament = Tournament(start_date=date.today())
    db_session.add(tournament)
    db_session.commit()

    assert db_session.query(Tournament).count() == 1


def test_create_round(db_session):
    tournament = Tournament(start_date=date.today())
    db_session.add(tournament)
    db_session.commit()

    round_1 = Round(round_number=1, tournament_id=tournament.id)
    db_session.add(round_1)
    db_session.commit()

    assert db_session.query(Round).count() == 1
    assert round_1.tournament == tournament


def test_create_match(db_session):
    tournament = Tournament(start_date=date.today())
    db_session.add(tournament)
    db_session.commit()

    round_1 = Round(round_number=1, tournament_id=tournament.id)
    db_session.add(round_1)
    db_session.commit()

    match = Match(round_id=round_1.id)
    db_session.add(match)
    db_session.commit()

    assert db_session.query(Match).count() == 1
    assert match.round == round_1


def test_create_team(db_session):
    match = Match()
    db_session.add(match)
    db_session.commit()

    team = Team(match_id=match.id, score=11)
    db_session.add(team)
    db_session.commit()

    assert db_session.query(Team).count() == 1
    assert team.match == match


def test_create_players_and_assign_to_team(db_session):
    match = Match()
    db_session.add(match)
    db_session.commit()

    team = Team(match_id=match.id, score=11)
    db_session.add(team)
    db_session.commit()

    player1 = Player(name="Alice", cumulative_score=0)
    player2 = Player(name="Bob", cumulative_score=0)

    team.players.append(player1)
    team.players.append(player2)
    db_session.commit()

    assert db_session.query(Player).count() == 2
    assert len(team.players) == 2
    assert player1 in team.players
    assert player2 in team.players


def test_players_inherit_team_score(db_session):
    match = Match()
    db_session.add(match)
    db_session.commit()

    team = Team(match_id=match.id, score=15)
    db_session.add(team)
    db_session.commit()

    player1 = Player(name="Charlie")
    player2 = Player(name="Dana")
    team.players.append(player1)
    team.players.append(player2)
    db_session.commit()

    for player in team.players:
        player.cumulative_score += team.score
    db_session.commit()

    assert player1.cumulative_score == 15
    assert player2.cumulative_score == 15


def test_create_full_tournament_structure(db_session, player_names):
    # Step 1: Create tournament
    tournament = Tournament(start_date=date.today())
    db_session.add(tournament)
    db_session.commit()

    players = [Player(name=name, cumulative_score=0) for name in player_names]
    db_session.add_all(players)
    db_session.commit()

    # Create rounds
    for round_number in range(1, tournament.rounds_count + 1):
        round_obj = Round(round_number=round_number, tournament_id=tournament.id)
        db_session.add(round_obj)
        db_session.commit()

        # Create matches
        for _ in range(6):
            match = Match(round_id=round_obj.id)
            db_session.add(match)
            db_session.commit()

            # Randomly assign players into teams
            random.shuffle(players)
            team1 = Team(match_id=match.id, score=random.randint(0, 21))
            team2 = Team(match_id=match.id, score=random.randint(0, 21))

            team1.players.extend(players[:2])
            team2.players.extend(players[2:4])

            db_session.add_all([team1, team2])
            db_session.commit()

    # Step 2: Read and print tournament structure from database
    tournament = db_session.query(Tournament).first()
    print(f"Tournament ID: {tournament.id}, Start Date: {tournament.start_date}")

    print("***")
    for round_obj in tournament.rounds:
        print(f"  Round {round_obj.round_number}")
        for match in round_obj.matches:
            print(f"    Match {match.id}")
            for team in match.teams:
                player_names = ", ".join(player.name for player in team.players)
                print(f"      Team {team.id} (Score: {team.score}): {player_names}")

    assert db_session.query(Tournament).count() == 1
    assert db_session.query(Round).count() == 10
    assert db_session.query(Match).count() == 60
    assert db_session.query(Team).count() == 120
    assert db_session.query(Player).count() == 24

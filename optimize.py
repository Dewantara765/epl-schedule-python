from scheduler import semi_mirror_schedule, has_derby_last_round, assign_home_away
from ranking import evaluate_schedule_simple
from config import name_to_id, teams

def evaluate_weights(weights, teams, derby_pairs, return_schedule=False):
    # generate schedule
    while True:
        schedule = semi_mirror_schedule(teams)
        if not has_derby_last_round(schedule, derby_pairs):
            break

    schedule = [
        [(name_to_id[a], name_to_id[b]) for (a,b) in rnd]
        for rnd in schedule
    ]

    final_schedule, penalties, team_difficulty = assign_home_away(schedule, teams, weights)

    if final_schedule is None:
        return 1e9
    
    ranking = evaluate_schedule_simple(final_schedule, teams, {
        "MCI":5,"ARS":5,"LIV":5,
        "AVL":4,"TOT":4,"CHE":4,
        "NEW":3,"MUN":3,"WHU":3,
        "CRY":2,"BHA":2,"BOU":2,
        "FUL":2,"WOL":2,"EVE":2,
        "BRE":1,"NFO":1,"LEI":1,
        "IPS":1,"SOU":1
    })

    top_teams = ["MCI","ARS","LIV"]

    # ubah ranking ke dict biar gampang akses
    ranking_dict = {team: score for team, score in ranking}

    top_penalty = 0
    avg = sum(ranking_dict.values()) / len(ranking_dict)

    for team in top_teams:
        score = ranking_dict[team]
        if score > avg:
            top_penalty += (score - avg)
        
    max_diff = max(score for _, score in ranking)
    min_diff = min(score for _, score in ranking)

    imbalance = max_diff - min_diff

    

    score = (
        10 * penalties["breaks"] +
        8 * penalties["big"] +
        6 * penalties["window"] +
        2 * penalties["fdb"] +
        3 * penalties["short_fdb"] +
        15 * top_penalty +
        12 * imbalance
    )


    if return_schedule:
        return score, final_schedule

    return score
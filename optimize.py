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

    # best_weights = best["weights"]

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

    
    objectives = {
        "breaks": penalties["breaks"],
        "big": penalties["big"],
        "window": penalties["window"],
        "fdb": penalties["fdb"],
        "short_fdb": penalties["short_fdb"],
        "top_penalty": top_penalty,
        "imbalance": imbalance
    }


    if return_schedule:
        return objectives, final_schedule

    return objectives, final_schedule

def dominates(a, b):
    better_or_equal = True
    strictly_better = False

    for key in a:
        if a[key] > b[key]:  # semua minimize
            better_or_equal = False
            break
        elif a[key] < b[key]:
            strictly_better = True

    return better_or_equal and strictly_better

def update_pareto(pareto_set, new_entry):
    new_pareto = []
    dominated = False

    for p in pareto_set:
        if dominates(p["obj"], new_entry["obj"]):
            dominated = True
            break
        elif dominates(new_entry["obj"], p["obj"]):
            continue
        else:
            new_pareto.append(p)

    if not dominated:
        new_pareto.append(new_entry)

    return new_pareto
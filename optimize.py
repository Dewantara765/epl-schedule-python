from scheduler import semi_mirror_schedule, has_derby_last_round, assign_home_away
from ranking import evaluate_schedule_simple
from config import name_to_id, teams

def big_match_balance_penalty(schedule, big_teams, id_to_name=None, debug=False):
    home_count = {team: 0 for team in big_teams}
    total_count = {team: 0 for team in big_teams}

    # =========================
    # HANYA PARUH PERTAMA
    # =========================
    first_half = schedule[:19]

    for rnd in first_half:
        for home, away in rnd:
            if home in big_teams and away in big_teams:
                home_count[home] += 1
                total_count[home] += 1
                total_count[away] += 1

    penalty = 0

    for team in big_teams:
        h = home_count[team]

        if h in [2, 3]:
            continue
        elif h in [1, 4]:
            penalty += 2
        else:
            penalty += 10

    # =========================
    # DEBUG
    # =========================
    if debug:
        print("\n=== BIG MATCH (FIRST HALF) ===")
        for team in big_teams:
            name = id_to_name[team] if id_to_name else team
            print(f"{name}: home={home_count[team]}")

    if debug:
        print("\nDETAIL MATCH:")
        for r, rnd in enumerate(first_half, 1):
            for home, away in rnd:
                if home in big_teams and away in big_teams:
                    print(f"R{r}: {id_to_name[home]} vs {id_to_name[away]}")

    return penalty

def evaluate_weights(weights, teams, derby_pairs, return_schedule=False):
    # generate schedule
    big_pairs = [
        ("ARS","CHE"), ("ARS","LIV"), ("ARS","MCI"), ("ARS","MUN"), ("ARS","TOT"),
        ("CHE","LIV"), ("CHE","MCI"), ("CHE","MUN"), ("CHE","TOT"),
        ("LIV","MCI"), ("LIV","MUN"), ("LIV","TOT"),
        ("MCI","MUN"), ("MCI","TOT"),
        ("MUN","TOT")
    ]
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

    result = final_schedule, penalties, team_difficulty

    if result is None:
        return float("inf")

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

    big_teams = ["MCI","ARS","LIV", "CHE","TOT","MUN"]

    # ubah ranking ke dict biar gampang akses
    # ranking_dict = {team: score for team, score in ranking}

    # big_penalty = 0
    # avg = sum(ranking_dict.values()) / len(ranking_dict)

    # for team in big_teams:
    #     score = ranking_dict[team]
    #     big_penalty += abs(score - avg)

    max_diff = max(score for _, score in ranking)
    min_diff = min(score for _, score in ranking)

    imbalance = max_diff - min_diff

    big_teams_names = ["MCI","ARS","LIV","CHE","MUN","TOT"]
    big_teams_ids = [name_to_id[t] for t in big_teams_names]

    big_balance = big_match_balance_penalty(final_schedule, big_teams_ids)

    # for team in big_teams:
    #     print(team, home_count[team])

    
    objectives = {
        "breaks": penalties["breaks"],
        "big": penalties["big"],
        "window": penalties["window"],
        "fdb": penalties["fdb"],
        "streak": penalties["streak_violation"],
        # "big_penalty": big_penalty,
        "imbalance": imbalance,
        "big_balance": big_balance,
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
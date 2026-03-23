
import random
from optimize import evaluate_weights
from ranking import evaluate_schedule_simple
from scheduler import semi_mirror_schedule, has_derby_last_round, assign_home_away
from config import teams, derby_pairs, id_to_name, name_to_id
from visual import plot_selected_teams

# =========================
# MAIN
# =========================
if __name__ == "__main__":


    best_score = 1e18
    best_weights = None

    for i in range(20):
        weights = {
            "breaks": random.randint(5, 15),
            "big": random.randint(5, 15),
            "window": random.randint(1, 10),
            "fdb": random.uniform(0.5, 3),
            "short_fdb": random.uniform(1, 5)
        }

        score = evaluate_weights(weights, teams, derby_pairs)

        print(f"Iter {i} → score={score:.2f}")

        if score < best_score:
            best_score = score
            best_weights = weights
            print("🔥 NEW BEST:", best_score, best_weights)

    # setelah loop
    print("\n=== BEST RESULT ===")
    print(best_score)
    print(best_weights)

# 🔥 ambil jadwal terbaik
    score, final_schedule = evaluate_weights(best_weights, teams, derby_pairs, return_schedule=True)

    while True:
        schedule = semi_mirror_schedule(teams)
        if not has_derby_last_round(schedule, derby_pairs):
            break

    schedule = [
        [(name_to_id[a], name_to_id[b]) for (a,b) in rnd]
        for rnd in schedule
    ]

    final_schedule, penalties, team_difficulty = assign_home_away(schedule, teams, weights)

    if final_schedule:
        for r, matches in enumerate(final_schedule):
            print(f"Round {r+1}")
            for home, away in matches:
                print(f"{id_to_name[home]} vs {id_to_name[away]}")
            print()
    else:
        print("No feasible schedule")

ranking = evaluate_schedule_simple(final_schedule, teams, {
        "MCI":5,"ARS":5,"LIV":5,
        "AVL":4,"TOT":4,"CHE":4,
        "NEW":3,"MUN":3,"WHU":3,
        "CRY":2,"BHA":2,"BOU":2,
        "FUL":2,"WOL":2,"EVE":2,
        "BRE":1,"NFO":1,"LEI":1,
        "IPS":1,"SOU":1
    })


print("\n=== RANKING KEUNTUNGAN JADWAL ===")
for i,(team,score) in enumerate(ranking,1):
    print(f"{i}. {team} → {score:.2f}")

plot_selected_teams(team_difficulty, teams, ["ARS", "CHE", "LIV", "MCI", "MUN", "TOT"])

    
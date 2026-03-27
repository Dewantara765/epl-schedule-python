
import random
from optimize import evaluate_weights, update_pareto
from ranking import evaluate_schedule_simple
from scheduler import semi_mirror_schedule, has_derby_last_round, assign_home_away
from config import teams, derby_pairs, id_to_name, name_to_id
from optimize import big_match_balance_penalty
import csv
# from visual import plot_selected_teams

# =========================
# SELECTOR (TARUH DI SINI)
# =========================
def select_solution(pareto_set):
    best_break = min(x["raw_obj"]["breaks"] for x in pareto_set)

    candidates = [
        x for x in pareto_set
        if x["raw_obj"]["breaks"] <= best_break + 3
    ]

    return min(candidates, key=lambda x: (
        x["raw_obj"]["big"],
        x["raw_obj"]["imbalance"],
        x["raw_obj"]["window"]
    ))

def export_schedule_to_csv(schedule, id_to_name, filename="schedule.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        
        # header
        writer.writerow(["round", "home", "away"])
        
        for r, matches in enumerate(schedule, 1):
            for home, away in matches:
                writer.writerow([
                    r,
                    id_to_name[home],
                    id_to_name[away]
                ])

    print(f"\n✅ Schedule exported ke {filename}")

def count_home_away_first_half(schedule, id_to_name=None, debug=False):
    home_count = {}
    away_count = {}

    # ambil paruh pertama
    first_half = schedule[:19]

    for rnd in first_half:
        for home, away in rnd:

            home_count[home] = home_count.get(home, 0) + 1
            away_count[away] = away_count.get(away, 0) + 1

            # pastikan semua tim tercatat
            if away not in home_count:
                home_count[away] = home_count.get(away, 0)
            if home not in away_count:
                away_count[home] = away_count.get(home, 0)

    # =========================
    # DEBUG PRINT
    # =========================
    if debug:
        print("\n=== HOME/AWAY FIRST HALF ===")
        for team in home_count:
            name = id_to_name[team] if id_to_name else team
            h = home_count.get(team, 0)
            a = away_count.get(team, 0)
            print(f"{name}: home={h}, away={a}")

    return home_count, away_count

# =========================
# MAIN
# =========================
if __name__ == "__main__":


    # best_score = 1e18
    # best_weights = None

    def normalize(obj):
        return {
            "breaks": obj["breaks"] / 200,
            "big": obj["big"] / 20,
            "window": obj["window"] / 40,
            "fdb": obj["fdb"] / 8000,
            # "big_penalty": obj["big_penalty"] / 30,
            "imbalance": obj["imbalance"] / 30
        }

    pareto_set = []
    for i in range(20):
        weights = {
            "breaks": random.randint(5, 15),
            "big": random.randint(5, 15),
            "window": random.randint(1, 10),
            "fdb": random.uniform(0.5, 3),
        }

        result = evaluate_weights(weights, teams, derby_pairs)

        if result is None:
            continue

        obj, schedule = result

        entry = {
            "weights": weights,
            "obj": normalize(obj),  # 🔥 pakai ini
            "raw_obj": obj,
            "schedule" : schedule
        }

        pareto_set = update_pareto(pareto_set, entry)

        print(f"Iter {i} → {obj}")

        if len(pareto_set) > 50:
            pareto_set = sorted(
                pareto_set,
                key=lambda x: sum(x["obj"].values())
            )[:50]

        # if score < best_score:
        #     best_score = score
        #     best_weights = weights
        #     print("🔥 NEW BEST:", best_score, best_weights)

    # # setelah loop
    # print("\n=== BEST RESULT ===")
    # print(best_score)
    # print(best_weights)

# 🔥 ambil jadwal terbaik
    # score, final_schedule = evaluate_weights(best_weights, teams, derby_pairs, return_schedule=True)



#     while True:
#         schedule = semi_mirror_schedule(teams)
#         if not has_derby_last_round(schedule, derby_pairs):
#             break

#     schedule = [
#         [(name_to_id[a], name_to_id[b]) for (a,b) in rnd]
#         for rnd in schedule
#     ]

#     final_schedule, penalties, team_difficulty = assign_home_away(schedule, teams, weights)

#     if final_schedule:
#         for r, matches in enumerate(final_schedule):
#             print(f"Round {r+1}")
#             for home, away in matches:
#                 print(f"{id_to_name[home]} vs {id_to_name[away]}")
#             print()
#     else:
#         print("No feasible schedule")

# ranking = evaluate_schedule_simple(final_schedule, teams, {
#         "MCI":5,"ARS":5,"LIV":5,
#         "AVL":4,"TOT":4,"CHE":4,
#         "NEW":3,"MUN":3,"WHU":3,
#         "CRY":2,"BHA":2,"BOU":2,
#         "FUL":2,"WOL":2,"EVE":2,
#         "BRE":1,"NFO":1,"LEI":1,
#         "IPS":1,"SOU":1
#     })


# print("\n=== RANKING KEUNTUNGAN JADWAL ===")
# for i,(team,score) in enumerate(ranking,1):
#     print(f"{i}. {team} → {score:.2f}")

print("\n=== PARETO FRONT ===")
for i, p in enumerate(pareto_set, 1):
    print(f"\nSolution {i}")
    print("Weights:", p["weights"])
    print("Objectives:", p["obj"])

best = select_solution(pareto_set)

# DEBUG FINAL SAJA


final_schedule = best["schedule"]


print("\n=== SELECTED SOLUTION ===")
print("Objectives:", best["raw_obj"])
print("Weights:", best["weights"])


for r, matches in enumerate(final_schedule):
    print(f"Round {r+1}")
    for home, away in matches:
        print(f"{id_to_name[home]} vs {id_to_name[away]}")
    print()

big_match_balance_penalty(
    best["schedule"],
    [name_to_id[t] for t in ["MCI","ARS","LIV","CHE","MUN","TOT"]],
    id_to_name=id_to_name,
    debug=True
)

count_home_away_first_half(
    final_schedule,
    id_to_name=id_to_name,
    debug=True
)




# plot_selected_teams(team_difficulty, teams, ["ARS", "CHE", "LIV", "MCI", "MUN", "TOT"])

    
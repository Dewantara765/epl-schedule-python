import random
from ortools.sat.python import cp_model

def circle_method(teams):
    n = len(teams)
    rounds = []
    team_list = teams[:]

    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            pairs.append((team_list[i], team_list[n - 1 - i]))
        rounds.append(pairs)

        team_list = [team_list[0]] + [team_list[-1]] + team_list[1:-1]

    return rounds

def is_big_match(a, b, big_pairs):
    return (a, b) in big_pairs or (b, a) in big_pairs

def semi_mirror_schedule(teams):
    first_half = circle_method(teams)

    # stabilkan awal
    head = first_half[:4]
    tail = first_half[4:]
    random.shuffle(tail)
    first_half = head + tail

    # mirror
    second_half = []
    for rnd in first_half:
        flipped = [(b, a) for (a, b) in rnd]
        second_half.append(flipped)

    # random shift (lebih fleksibel)
    shift = random.randint(3, len(first_half)-3)
    second_half = second_half[shift:] + second_half[:shift]

    return first_half + second_half

def has_derby_last_round(schedule, derby_pairs):
    last_round = schedule[-1]
    derby_set = set(tuple(sorted(p)) for p in derby_pairs)

    for (a,b) in last_round:
        if tuple(sorted((a,b))) in derby_set:
            return True
    return False

def assign_home_away(schedule, teams, weights):
    model = cp_model.CpModel()

    R = len(schedule)
    N = len(teams)
    name_to_id = {t: i for i, t in enumerate(teams)}

    # =========================
    # DATA
    # =========================
    derby_pairs = [("ARS","TOT"), ("CHE","FUL"), ("EVE","LIV"), ("MCI","MUN")]
    derby_pairs = [(name_to_id[a], name_to_id[b]) for a,b in derby_pairs]

    big_matches = [
        ("ARS","CHE"), ("ARS","LIV"), ("ARS","MCI"), ("ARS","MUN"), ("ARS","TOT"),
        ("CHE","LIV"), ("CHE","MCI"), ("CHE","MUN"), ("CHE","TOT"),
        ("LIV","MCI"), ("LIV","MUN"), ("LIV","TOT"),
        ("MCI","MUN"), ("MCI","TOT"),
        ("MUN","TOT")
    ]

    strength = {
        "MCI":5,"ARS":5,"LIV":5,
        "AVL":4,"TOT":4,"CHE":4,
        "NEW":3,"MUN":3,"WHU":3,
        "CRY":2,"BHA":2,"BOU":2,
        "FUL":2,"WOL":2,"EVE":2,
        "BRE":1,"NFO":1,"LEI":1,
        "IPS":1,"SOU":1
    }

    strength = {name_to_id[k]: v for k,v in strength.items()}
    big_matches = [(name_to_id[a], name_to_id[b]) for a,b in big_matches]
    big_set = set(tuple(sorted(p)) for p in big_matches)

    # =========================
    # VARIABLES
    # =========================
    y = {}
    h = {}
    big = {}
    breaks = {}
    difficulty = {}
    pair_matches = {}
    team_difficulty = {}


    for r in range(R):
        for m, (a,b) in enumerate(schedule[r]):
            y[r,m] = model.NewBoolVar(f"y_{r}_{m}")

    for i in range(N):
        for r in range(R):
            h[i,r] = model.NewBoolVar(f"h_{i}_{r}")
            big[i,r] = model.NewBoolVar(f"big_{i}_{r}")
            difficulty[i,r] = model.NewIntVar(0, 20, f"diff_{i}_{r}")

    for i in range(N):
        for r in range(R-1):
            breaks[i,r] = model.NewBoolVar(f"break_{i}_{r}")

    # =========================
    # DIFFICULTY (WITH HOME ADV)
    # =========================
    SCALE = 2
    HOME_ADV = 1  # = 0.5 real

    strength = {k: v * SCALE for k,v in strength.items()}

    for r in range(R):
        for m, (a,b) in enumerate(schedule[r]):
            sa = strength[a]
            sb = strength[b]

            model.Add(difficulty[a,r] == sb - HOME_ADV).OnlyEnforceIf(y[r,m])
            model.Add(difficulty[b,r] == sa + HOME_ADV).OnlyEnforceIf(y[r,m])

            model.Add(difficulty[a,r] == sb + HOME_ADV).OnlyEnforceIf(y[r,m].Not())
            model.Add(difficulty[b,r] == sa - HOME_ADV).OnlyEnforceIf(y[r,m].Not())

    # =========================
    # BIG MATCH
    # =========================
    for r in range(R):
        for m, (a,b) in enumerate(schedule[r]):
            if tuple(sorted((a,b))) in big_set:
                model.Add(big[a,r] == 1)
                model.Add(big[b,r] == 1)

    for i in range(N):
        for r in range(R):
            involved = []
            for (a,b) in schedule[r]:
                if i == a or i == b:
                    involved.append(1 if tuple(sorted((a,b))) in big_set else 0)
            model.Add(big[i,r] == sum(involved))

    big_penalties = []
    for i in range(N):
        for r in range(R-1):
            v = model.NewBoolVar(f"big_violation_{i}_{r}")
            model.Add(big[i,r] + big[i,r+1] > 1).OnlyEnforceIf(v)
            model.Add(big[i,r] + big[i,r+1] <= 1).OnlyEnforceIf(v.Not())
            big_penalties.append(v)

    # =========================
    # PAIR CONSISTENCY
    # =========================
    for r in range(R):
        for m, (a,b) in enumerate(schedule[r]):
            key = tuple(sorted([a,b]))
            pair_matches.setdefault(key, []).append((r,m,a,b))

    for key, matches in pair_matches.items():
        if len(matches) == 2:
            (r1,m1,a1,b1), (r2,m2,a2,b2) = matches
            if a1 == a2:
                model.Add(y[r1,m1] + y[r2,m2] == 1)
            else:
                model.Add(y[r1,m1] + (1 - y[r2,m2]) == 1)

    # =========================
    # LINK HOME
    # =========================
    for r in range(R):
        for i in range(N):
            expr = []
            for m, (a,b) in enumerate(schedule[r]):
                if i == a:
                    expr.append(y[r,m])
                elif i == b:
                    expr.append(1 - y[r,m])
            model.Add(h[i,r] == sum(expr))

    for i in range(N):
        model.Add(sum(h[i,r] for r in range(19)) >= 9)
        model.Add(sum(h[i,r] for r in range(19)) <= 10)

    # for i in range(N):
    #     model.Add(h[i,0] != h[i,1])

    # for i in range(N):
    #     model.Add(h[i,R-2] != h[i,R-1])

    # =========================
    # CONSTRAINTS
    # =========================
    violations = []

    for i in range(N):
        for r in range(R-2):
            v = model.NewBoolVar(f"v_{i}_{r}")

            model.Add(h[i,r] + h[i,r+1] + h[i,r+2] <= 2 + v)
            model.Add(h[i,r] + h[i,r+1] + h[i,r+2] >= 1 - v)

            violations.append(v)

    for (a,b) in derby_pairs:
        for r in range(R):
            model.Add(h[a,r] + h[b,r] == 1)

    # =========================
    # PENALTIES
    # =========================
    half_penalties = []
    half = R // 2

    for i in range(N):
        home_first_half = sum(h[i,r] for r in range(half))

        over = model.NewIntVar(0, half, f"over_{i}")
        under = model.NewIntVar(0, half, f"under_{i}")

        model.Add(home_first_half - (half//2 + 1) <= over)
        model.Add((half//2) - home_first_half <= under)

        half_penalties += [over, under]

    start_end_penalties = []
    for i in range(N):
        v_start = model.NewBoolVar(f"v_start_{i}")
        v_end = model.NewBoolVar(f"v_end_{i}")

        model.Add(h[i,0] == h[i,1]).OnlyEnforceIf(v_start)
        model.Add(h[i,R-2] == h[i,R-1]).OnlyEnforceIf(v_end)

        start_end_penalties += [v_start, v_end]

    window_penalties = []
    for i in range(N):
        for r in range(R-4):
            home_count = sum(h[i,r+k] for k in range(5))

            over = model.NewIntVar(0,5,f"over_{i}_{r}")
            under = model.NewIntVar(0,5,f"under_{i}_{r}")

            model.Add(home_count - 3 <= over)
            model.Add(2 - home_count <= under)

            window_penalties += [over, under]

        same = model.NewBoolVar(f"same_{i}_{r}")

        model.Add(h[i,r] == h[i,r+1]).OnlyEnforceIf(same)
        model.Add(h[i,r] != h[i,r+1]).OnlyEnforceIf(same.Not())

        model.Add(breaks[i,r] == same)

    # FDB
    fdb_penalties = []
    window = 5

    for i in range(N):
        for r in range(R - window + 1):
            total = sum(difficulty[i, r+k] for k in range(window))
            avg = window * 3

            dev = model.NewIntVar(0, 50, f"fdb_dev_{i}_{r}")

            model.Add(total - avg <= dev)
            model.Add(avg - total <= dev)

            fdb_penalties.append(dev)

    # EXTRA: short window (VERY IMPORTANT)
    # short_fdb_penalties = []
    # window = 3

    # for i in range(N):
    #     for r in range(R-window+1):
    #         total = sum(difficulty[i,r+k] for k in range(window))
    #         avg = window * 3

    #         over = model.NewIntVar(0,30,f"s_fdb_over_{i}_{r}")
    #         under = model.NewIntVar(0,30,f"s_fdb_under_{i}_{r}")

    #         model.Add(total - avg <= over)
    #         model.Add(avg - total <= under)

    #         short_fdb_penalties += [over, under]
    big_window_penalties = []
    window = 4

    for i in range(N):
        for r in range(R-window+1):
            total_big = sum(big[i,r+k] for k in range(window))

            excess = model.NewIntVar(0, window, f"big_excess_{i}_{r}")
            model.Add(total_big - 2 <= excess)  # max 2 big dalam 4 round

            big_window_penalties.append(excess)
    weak_penalties = []

    for i in range(N):
        if strength[i] <= 4:  # karena sudah di-scale (2x)
            for r in range(R-2):
                total = sum(difficulty[i,r+k] for k in range(3))

                excess = model.NewIntVar(0,50,f"weak_excess_{i}_{r}")
                model.Add(total - 18 <= excess)  # threshold lebih ketat

                weak_penalties.append(excess)
    
    for i in range(N):
        for r in range(R-3):
            model.Add(h[i,r] + h[i,r+1] + h[i,r+2] <= 2)



    # =========================
    # OBJECTIVE
    # =========================
    model.Minimize(
        weights["breaks"] * sum(breaks.values()) +
        weights["big"] * (sum(big_penalties) + sum(big_window_penalties)) +
        weights["window"] * sum(window_penalties) +
        weights["fdb"] * sum(fdb_penalties) 
        # weights["short_fdb"] * sum(short_fdb_penalties)
    )

    

    # =========================
    # SOLVE
    # =========================
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5



    def sum_bool(vars_dict):
        return sum(solver.Value(v) for v in vars_dict)

    result = solver.Solve(model)


    if result in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        final_schedule= []
        for r in range(R):
            round_matches = []
            for m, (a,b) in enumerate(schedule[r]):
                if solver.Value(y[r,m]) == 1:
                    round_matches.append((a,b))
                else:
                    round_matches.append((b,a))
            final_schedule.append(round_matches)

        for i in range(N):
            team_difficulty[i] = [
                solver.Value(difficulty[i, r]) for r in range(R)
            ]
        
        return final_schedule, {
            "breaks": sum(solver.Value(v) for v in breaks.values()),
            "big": sum(solver.Value(v) for v in big_penalties),
            "window": sum(solver.Value(v) for v in window_penalties),
            "fdb": sum(solver.Value(v) for v in fdb_penalties),
           "streak_violation": sum(solver.Value(v) for v in violations)
            # "short_fdb": sum(solver.Value(v) for v in short_fdb_penalties)
        }, team_difficulty
    return None

    
    
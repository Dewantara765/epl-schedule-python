from collections import defaultdict

def evaluate_schedule_simple(schedule, teams, strength):
    name_to_id = {t:i for i,t in enumerate(teams)}
    id_to_name = {i:t for t,i in name_to_id.items()}
    N = len(teams)
    R = len(schedule)

    # convert strength
    strength = {name_to_id[k]: v for k,v in strength.items()}

    # define big matches
    big_matches = [
        ("ARS","CHE"), ("ARS","LIV"), ("ARS","MCI"), ("ARS","MUN"), ("ARS","TOT"),
        ("CHE","LIV"), ("CHE","MCI"), ("CHE","MUN"), ("CHE","TOT"),
        ("LIV","MCI"), ("LIV","MUN"), ("LIV","TOT"),
        ("MCI","MUN"), ("MCI","TOT"),
        ("MUN","TOT")
    ]
    big_set = set(tuple(sorted((name_to_id[a], name_to_id[b]))) for a,b in big_matches)

    HOME_ADV = 0.5

    # track per tim
    difficulty = defaultdict(list)
    home = defaultdict(list)
    big_flag = defaultdict(list)

    for r in range(R):
        for (a,b) in schedule[r]:
            sa = strength[a]
            sb = strength[b]

            # home/away difficulty
            difficulty[a].append(sb - HOME_ADV)
            difficulty[b].append(sa + HOME_ADV)

            # home/away tracking
            home[a].append(1)
            home[b].append(0)

            # big match
            is_big = 1 if tuple(sorted((a,b))) in big_set else 0
            big_flag[a].append(is_big)
            big_flag[b].append(is_big)

    scores = {}
    for i in range(N):
        # 1. Strength difficulty
        SD = sum(difficulty[i])

        # 2. Home/away balance
        HA = abs(sum(home[i]) - R/2)

        # 3. Streak penalty
        streak = 1
        ST = 0
        for r in range(1, R):
            if home[i][r] == home[i][r-1]:
                streak += 1
            else:
                if streak > 2:
                    ST += (streak-2)**2
                streak = 1
        if streak > 2:
            ST += (streak-2)**2

        # 4. Big match clustering
        BM = 0
        for r in range(R-1):
            if big_flag[i][r] and big_flag[i][r+1]:
                BM += 1

        total_score = SD + 2*HA + 3*ST + 4*BM
        scores[id_to_name[i]] = total_score

    # ranking (lower = better)
    ranking = sorted(scores.items(), key=lambda x: x[1])
    return ranking
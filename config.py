from ranking import evaluate_schedule_simple
teams = [
        "LEI","MCI","BRE","BOU","ARS","EVE","CRY","WHU","NEW","MUN",
        "NFO","BHA","IPS","FUL","TOT","AVL","SOU","CHE","WOL","LIV"
    ]

derby_pairs = [("ARS","TOT"), ("CHE","FUL"), ("EVE","LIV"), ("MCI","MUN")]

name_to_id = {t:i for i,t in enumerate(teams)}
id_to_name = {i:t for t,i in name_to_id.items()}

# ranking = evaluate_schedule_simple(final_schedule, teams, )
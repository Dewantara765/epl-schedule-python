import matplotlib.pyplot as plt

def plot_selected_teams(team_difficulty, teams, selected):
    for i, team in enumerate(teams):
        if team in selected:
            plt.plot(team_difficulty[i], label=team)

    plt.xlabel("Round")
    plt.ylabel("Difficulty")
    plt.title("Selected Teams Difficulty")
    plt.legend()
    plt.show()
    

def plot_team_difficulty(team_difficulty, teams):
    for i, diff in team_difficulty.items():
        plt.plot(diff, label=teams[i])

    plt.xlabel("Round")
    plt.ylabel("Difficulty")
    plt.title("Fixture Difficulty per Team")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
    
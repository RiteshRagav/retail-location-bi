def normalize(value, max_value):
    if max_value == 0:
        return 0
    return min((value / max_value) * 100, 100)


def compute_viability(demand, competition, access, diversity):
    return round(
        (0.35 * demand)
        - (0.30 * competition)
        + (0.20 * access)
        + (0.15 * diversity),
        2
    )


def classify(score):
    if score >= 75:
        return "Strongly Recommended"
    elif score >= 50:
        return "Promising"
    else:
        return "Risky"

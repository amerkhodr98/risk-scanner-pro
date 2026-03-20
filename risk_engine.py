def calculate_risk(country, weight, route, company):
    score = 0

    if country in ["Colombia", "Unknown"]:
        score += 30
    if route == "Unusual":
        score += 25
    if weight < 100 or weight > 3000:
        score += 20
    if company == "New":
        score += 25

    return score

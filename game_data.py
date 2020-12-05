import requests

url = "https://epam-botchallenge.com/codenjoy-balancer/rest/game/settings/get"
controls = requests.get(url).json()[0]

for control in controls:
    print(f"{control}\t\t= controls[\"{control}\"]")
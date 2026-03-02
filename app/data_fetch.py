import requests

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def fetch_pois(lat, lon, radius=1000):
    query = f"""
    [out:json];
    (
      node(around:{radius},{lat},{lon})["amenity"];
    );
    out;
    """

    response = requests.post(OVERPASS_URL, data={"data": query})
    data = response.json()

    return data.get("elements", [])

import json
import os

DATA_FILE = "parcels.json"


def load_parcels():
    """Load the parcel list from disk. Returns an empty list if the file is missing or corrupted"""
    if not os.path.exists(DATA_FILE):
        print("warning: parcel.json not found. Starting with an empty parcel list.")
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("warning: parcels.json appears to be damaged and could not be read.")
        print("starting with an empty list. Your old file has not been deleted")
        return []


def save_parcels(parcels):
    """write the parcel list to disk as json"""
    with open(DATA_FILE, "w") as f:
        json.dump(parcels, f, indent=2)


def build_index(parcels):
    """Build a dictionary mapping tracking_code to parcel, for instant lookup"""
    index = {}
    for parcel in parcels:
        index[parcel["tracking_code"]] = parcel
    return index


def build_city_index(parcels):
    """Build a dictionary mapping destination city -> list of parcels heading there."""
    city_index = {}
    for parcel in parcels:
        city = parcel["destination"]
        city_index.setdefault(city, []).append(parcel)
    return city_index

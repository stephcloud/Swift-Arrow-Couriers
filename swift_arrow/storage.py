import hashlib
import json
import os

DATA_FILE = "parcels.json"
SEAL_FILE = "parcels.seal"


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


def build_status_index(parcels):
    """Build a dictionary mapping status -> list of parcels with that status."""
    status_index = {}
    for parcel in parcels:
        status = parcel["status"]
        status_index.setdefault(status, []).append(parcel)
    return status_index


def compute_seal():
    """Compute a fingerprint of the current contents of parcels.json."""
    with open(DATA_FILE, "rb") as f:
        contents = f.read()
    return hashlib.sha256(contents).hexdigest()


def save_seal():
    """Write the current fingerprint to disk."""
    seal = compute_seal()
    with open(SEAL_FILE, "w") as f:
        f.write(seal)


def verify_seal():
    """Check the current file against the saved fingerprint.
    Returns True if they match, False if they don't, None if no seal exists yet."""
    if not os.path.exists(SEAL_FILE):
        return None

    with open(SEAL_FILE, "r") as f:
        saved_seal = f.read().strip()

    current_seal = compute_seal()
    return current_seal == saved_seal

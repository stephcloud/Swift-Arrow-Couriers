import time


def get_parcel_by_code(index, code):
    """Look up one parcel by tracking code. Returns (code_num, message, data, elapsed_ms)"""
    start = time.perf_counter()
    parcel = index.get(code)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if parcel is None:
        return 404, f"There is no parcel {code}", None, elapsed_ms
    return 200, f"found in {elapsed_ms:.3f} ms", parcel, elapsed_ms


def create_parcel(
    parcels,
    index,
    tracking_code,
    sender,
    receiver,
    origin,
    destination,
    weight_kg,
    date_shipped,
):
    if tracking_code in index:
        return 400, f"parcel {tracking_code} already exists", None

    new_parcel = {
        "tracking_code": tracking_code,
        "sender": sender,
        "receiver": receiver,
        "origin": origin,
        "destination": destination,
        "status": "at station",
        "weight_kg": weight_kg,
        "date_shipped": date_shipped,
    }
    parcels.append(new_parcel)
    index[tracking_code] = new_parcel
    return 201, f"Created parcel {tracking_code}", new_parcel


def update_parcel(index, code, status=None, destination=None):
    parcel = index.get(code)
    if parcel is None:
        return 404, f"There is no parcel {code}", None

    if status is not None:
        parcel["status"] = status

    if destination is not None:
        parcel["destination"] = destination

    return 200, f"parcel {code} updated", parcel


def delete_parcel(parcels, index, code):
    parcel = index.get(code)
    if parcel is None:
        return 404, f"There is no parcel {code}", None

    parcels.remove(parcel)
    del index[code]
    return 200, f"Parcel {code} deleted", None

from swift_arrow import auth, storage, parcels, cache


def parse_slip(slip):
    parts = slip.strip().split()
    if len(parts) < 2:
        return None, None, None, None

    verb = parts[0].upper()
    resource = parts[1].lower()
    code_or_city = None
    extra = None

    if len(parts) >= 3:
        if parts[2].lower() == "to" and len(parts) >= 4:
            extra = parts[3]
        else:
            code_or_city = parts[2]

    return verb, resource, code_or_city, extra


def handle_slip(
    verb, resource, code_or_city, extra, data, index, city_index, user_info
):
    if resource != "parcel" and resource != "parcels":
        return (
            400,
            "I cannot read this slip. The verbs are GET, POST, PUT, DELETE.",
            None,
        )

    if verb == "GET" and resource == "parcel" and code_or_city:
        cache_key = f"parcel:{code_or_city}"
        cached = cache.get(cache_key)
        if cached is not None:
            return 200, "Found (from the tray)", cached

        code, message, payload, _ = parcels.get_parcel_by_code(index, code_or_city)
        if code == 200:
            cache.set(cache_key, payload)
        return code, message, payload

    if verb == "GET" and resource == "parcels" and extra:
        cache_key = f"city:{extra}"
        cached = cache.get(cache_key)
        if cached is not None:
            return 200, f"{len(cached)} parcels (from the tray)", cached[:5]

        matches = city_index.get(extra, [])
        cache.set(cache_key, matches)
        return 200, f"{len(matches)} parcels found", matches[:5]

    if verb == "POST" and resource == "parcel":
        tracking_code = input("Tracking code: ").strip()
        sender = input("sender: ").strip()
        receiver = input("receiver: ").strip()
        origin = input("origin: ").strip()
        destination = input("Destination: ").strip()
        weight_kg = float(input("weight (kg): ").strip())
        date_shipped = input("Date shipped (YYYY-MM-DD): ").strip()
        result = parcels.create_parcel(
            data,
            index,
            tracking_code,
            sender,
            receiver,
            origin,
            destination,
            weight_kg,
            date_shipped,
        )
        cache.clear()
        city_index.clear()
        city_index.update(storage.build_city_index(data))
        return result

    if verb == "PUT" and resource == "parcel" and code_or_city:
        new_status = input("New status (leave blank to skip): ").strip()
        new_destination = input("New destination (leave blank to skip): ").strip()
        result = parcels.update_parcel(
            index,
            code_or_city,
            status=new_status or None,
            destination=new_destination or None,
        )
        cache.clear()
        city_index.clear()
        city_index.update(storage.build_city_index(data))
        return result

    if verb == "DELETE" and resource == "parcel" and code_or_city:
        if not auth.is_station_master(user_info):
            return (
                403,
                "Clerks may not delete parcels. Speak to the Station Master.",
                None,
            )
        result = parcels.delete_parcel(data, index, code_or_city)
        cache.clear()
        city_index.clear()
        city_index.update(storage.build_city_index(data))
        return result

    return 400, "I cannot read this slip.", None


def sign_in_flow():
    print("--- THE GRILLE (sign in first) ---")
    username = input("Username: ").strip()
    password = input("password: ").strip()

    if not auth.check_credentials(username, password):
        print("401 incorrect username or password")
        return None

    token = auth.issue_token(username)
    position = auth.get_position(username)
    print(f"200 Welcome, {username} ({position})")
    print(f"your day pass: {token}")
    return token


def main():
    print("SWIFT ARROW COURIERS - TRACKING WINDOW")
    data = storage.load_parcels()
    index = storage.build_index(data)
    city_index = storage.build_city_index(data)

    token = sign_in_flow()
    if token is None:
        return

    while True:
        slip = input("\npass slip (or 'exit'): ").strip()
        if slip.lower() == "exit":
            auth.revoke_token(token)
            print("The window closes")
            break

        user_info = auth.validate_token(token)
        if user_info is None:
            print("401 your day pass is no longer valid. please sign in again")
            token = sign_in_flow()
            if token is None:
                break
            continue

        verb, resource, code_or_city, extra = parse_slip(slip)
        if verb is None:
            code, message, payload = 400, "I cannot read this slip", None
        else:
            code, message, payload = handle_slip(
                verb, resource, code_or_city, extra, data, index, city_index, user_info
            )

        print(f"{code} - {message}")
        if payload is not None:
            print(payload)

        if code in (200, 201) and verb in ("POST", "PUT", "DELETE"):
            storage.save_parcels(data)


if __name__ == "__main__":
    main()

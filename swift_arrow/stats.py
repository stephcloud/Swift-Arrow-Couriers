QUERY_COUNTS = {}


def record_query(code):
    """Record that a tracking code was looked up."""
    QUERY_COUNTS[code] = QUERY_COUNTS.get(code, 0) + 1


def most_wanted(top_n=10):
    """Return the top_n most-queried tracking codes, as (code, count) pairs, most first."""
    return sorted(QUERY_COUNTS.items(), key=lambda item: item[1], reverse=True)[:top_n]

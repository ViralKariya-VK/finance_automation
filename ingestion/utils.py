import hashlib


def generate_hash(date, description, amount):
    """
    Creates a unique fingerprint for a transaction row.
    Used to detect and prevent duplicate uploads.
    
    We lowercase and strip the description so that
    "Swiggy Order" and "swiggy order" are treated as the same row.
    """
    raw = f"{date}_{description.lower().strip()}_{amount}"
    return hashlib.sha256(raw.encode()).hexdigest()
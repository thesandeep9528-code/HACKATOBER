def get_initials(full_name):
    """
    Returns the initials of a user based on their full name.
    Examples:
    - "Rahul Kumar" -> "RK"
    - "Rahul Kumar Singh" -> "RS" (First + Last)
    - "Rahul" -> "RA" (First two letters if only one name)
    - "" -> ""
    """
    if not full_name:
        return ""

    parts = full_name.strip().split()

    if not parts:
        return ""

    # If user has 2 or more names (e.g., "Rahul Kumar"), take first letter of first and last name
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()

    # If user has only 1 name (e.g., "Rahul"), take first two letters
    if len(parts[0]) > 1:
        return parts[0][:2].upper()

    # Fallback for single letter names
    return parts[0][0].upper()

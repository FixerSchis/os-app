def mask_email(email: str) -> str:
    """
    Mask an email address for privacy.
    Format: tes****@address.com (hiding exactly how many characters were obscured)

    Examples:
    - testemailperson@address.com -> tes****@address.com
    - ab@example.com -> a****@example.com
    - xyz@domain.org -> x****@domain.org
    - a@test.com -> a****@test.com
    """
    if not email or "@" not in email:
        return email or ""

    local_part, domain = email.split("@", 1)

    if len(local_part) <= 3:
        # For very short local parts, just show first character
        masked_local = local_part[0] + "****"
    else:
        # Show first 3 characters, then mask the rest
        masked_local = local_part[:3] + "****"

    return f"{masked_local}@{domain}"

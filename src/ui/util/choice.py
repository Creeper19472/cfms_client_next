def normalize_always_choice(choice: str | None) -> str | None:
    """Convert 'always_*' choices to their single-action equivalents.

    Args:
        choice: User choice which may be 'overwrite', 'skip', 'always_overwrite',
                'always_skip', or None

    Returns:
        Normalized choice: 'overwrite', 'skip', or None
    """
    if choice == "always_overwrite":
        return "overwrite"
    elif choice == "always_skip":
        return "skip"
    return choice

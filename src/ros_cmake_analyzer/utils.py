

def key_val_list_to_dict(key_values: list[str]) -> dict[str, str]:
    """Convert a list of key, val pairs into a dict.

    Parameters
    ----------
    key_values: List[str]
        List of alternating key, value pairs in a list

    Returns
    -------
    Dict[str, str]
        A dictionary of key, value entries

    """
    assert len(key_values) % 2 == 0
    key_list = key_values[::2]
    value_list = key_values[1::2]
    return dict(zip(key_list, value_list, strict=True))

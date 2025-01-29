import pathlib


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


def has_python_shebang(file_path: pathlib.Path) -> bool:
    if not file_path.is_file():
        return False
    # is the file executable?
    if not (file_path.stat().st_mode & 0o111):
        return False
    with file_path.open("rb") as file:
        first_line = file.readline()
        return first_line.startswith(b"#!") and b"python" in first_line

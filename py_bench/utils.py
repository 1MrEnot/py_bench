def rjust_fit_string(string: str, width: int, fill_char: str = ' ', filler: str = '...', last_symbol_count: int = 2):
    return _fit_string(str.rjust, string, width, fill_char, filler, last_symbol_count)

def ljust_fit_string(string: str, width: int, fill_char: str = ' ', filler: str = '...', last_symbol_count: int = 2):
    return _fit_string(str.ljust, string, width, fill_char, filler, last_symbol_count)

def _fit_string(justifier: callable, string: str, width: int, fill_char: str, filler: str, last_symbol_count: int):
    n = len(string)
    if n <= width:
        return justifier(string, width, fill_char)

    res = f"{string[:width-last_symbol_count-len(filler)]}{filler}{string[-last_symbol_count:]}"
    assert len(res) == width, 'expected fit string len equal to provided width'
    return res

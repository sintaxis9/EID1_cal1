def clean_rut(rut: str) -> str:
    return ''.join(filter(str.isdigit, rut))


def format_rut_from_digits(digs8: list[int], check: str) -> str:
    s8 = ''.join(str(d) for d in digs8)
    if len(s8) != 8:
        return s8 + (("-" + check) if check else "")
    if check:
        return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}-{check}"
    else:
        return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}"


def extract_first8_digits(rut: str) -> list[int]:
    clean = clean_rut(rut)
    return [int(d) for d in clean[:8]]


def extract_check_digit(rut: str) -> str:
    clean = clean_rut(rut)
    return clean[8:] if len(clean) > 8 else ""

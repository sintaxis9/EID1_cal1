# services/rut_helper.py

def clean_rut(rut: str) -> str:
    """
    Devuelve sólo los dígitos del RUT en un string.
    Ejemplo: "12.345.678-9" → "123456789"
    """
    return ''.join(filter(str.isdigit, rut))


def format_rut_from_digits(digs8: list[int], check: str) -> str:
    """
    A partir de una lista de 8 dígitos [d1..d8] y un dígito verificador opcional check,
    devuelve un RUT en formato "XX.XXX.XXX-Y" (si check existe) o "XX.XXX.XXX" (si no hay check).
    """
    s8 = ''.join(str(d) for d in digs8)
    if len(s8) != 8:
        return s8 + (("-" + check) if check else "")
    if check:
        return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}-{check}"
    else:
        return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}"


def extract_first8_digits(rut: str) -> list[int]:
    """
    Extrae los primeros 8 dígitos numéricos de un RUT.  
    Ejemplo: "12.345.678-9" → [1,2,3,4,5,6,7,8]
    """
    clean = clean_rut(rut)
    return [int(d) for d in clean[:8]]


def extract_check_digit(rut: str) -> str:
    """
    Si el RUT tiene dígito verificador (o más de un dígito tras los 8),
    lo devuelve como string. Ej: "12345678-9" → "9". Si no hay dígito extra, devuelve "".
    """
    clean = clean_rut(rut)
    return clean[8:] if len(clean) > 8 else ""

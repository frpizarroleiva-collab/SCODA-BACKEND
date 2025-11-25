def validar_run(run: str) -> bool:
    """
    Valida un RUN/RUT chileno.
    Acepta cualquier formato:
    - 12.345.678-5
    - 12345678-5
    - 12345678K
    - 12.345.678 K
    """

    if not run:
        return False

    # Normalizar: quitar puntos, guiones y espacios
    run = run.replace(".", "").replace("-", "").replace(" ", "").upper()

    # Debe tener al menos 2 caracteres (cuerpo + DV)
    if len(run) < 2:
        return False

    cuerpo = run[:-1]
    dv = run[-1]

    # Cuerpo debe ser solo números
    if not cuerpo.isdigit():
        return False

    # Calcular DV real
    suma = 0
    multiplo = 2

    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo > 7:
            multiplo = 2

    resto = suma % 11
    dv_calculado = str(11 - resto)

    # Ajustar DV según reglas chilenas
    if dv_calculado == "11":
        dv_calculado = "0"
    elif dv_calculado == "10":
        dv_calculado = "K"

    return dv == dv_calculado

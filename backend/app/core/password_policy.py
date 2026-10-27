"""Política de contraseñas (NIST 800-63B): longitud + lista de contraseñas comunes + no derivadas del correo.
No se imponen reglas de composición arbitrarias (empeoran la calidad real)."""
from app.core.exceptions import AppError

MIN_LENGTH, MAX_LENGTH = 12, 128
COMMON = {
    "password1234", "contrasena123", "contraseña123", "123456789012", "qwertyuiop12", "abcdefghijkl", "kawsay123456",
    "kawsayai1234", "administrador", "administrator1", "docente123456", "profesor12345", "letmein12345", "iloveyou1234",
    "welcome12345", "123123123123", "111111111111", "000000000000", "passw0rd1234", "changeme1234", "cambiame12345",
}


class WeakPassword(AppError):
    status_code = 422
    code = "weak_password"


def check_password_policy(password: str, email: str | None = None, display_name: str | None = None) -> None:
    if len(password) < MIN_LENGTH or len(password) > MAX_LENGTH:
        raise WeakPassword(f"La contraseña debe tener entre {MIN_LENGTH} y {MAX_LENGTH} caracteres")
    low = password.casefold()
    if low in COMMON or len(set(low)) < 5:
        raise WeakPassword("La contraseña es demasiado común o repetitiva")
    if email and email.split("@")[0].casefold() in low and len(email.split("@")[0]) >= 4:
        raise WeakPassword("La contraseña no debe contener tu correo")
    if display_name and len(display_name) >= 4 and display_name.casefold().replace(" ", "") in low.replace(" ", ""):
        raise WeakPassword("La contraseña no debe contener tu nombre")

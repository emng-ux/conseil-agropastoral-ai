"""Détection simple de la connectivité Internet, pour le fonctionnement hybride
(en ligne / edge-hors ligne). Ne bloque jamais l'application : en cas de doute,
on considère qu'on est hors ligne et on retombe sur le mode formulaire local.
"""
import socket


def is_online(host: str = "8.8.8.8", port: int = 53, timeout: float = 1.5) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False

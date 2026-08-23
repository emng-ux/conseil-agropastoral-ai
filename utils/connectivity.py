"""Détection simple de la connectivité Internet, pour le fonctionnement hybride
(en ligne / edge-hors ligne). Ne bloque jamais l'application : en cas de doute,
on considère qu'on est hors ligne et on retombe sur le mode formulaire local.
"""
import socket


def is_online(timeout: float = 2.0) -> bool:
    """Teste la connectivité sur le port HTTPS (443) de plusieurs hôtes bien
    connus, plutôt que le port DNS (53) — ce dernier est souvent bloqué par
    des pare-feux/routeurs même quand Internet fonctionne normalement par
    ailleurs (navigation web classique), ce qui donnait de faux négatifs."""
    hosts = [("1.1.1.1", 443), ("8.8.8.8", 443), ("api.anthropic.com", 443)]
    for host, port in hosts:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except OSError:
            continue
    return False

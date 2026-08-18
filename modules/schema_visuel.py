"""Génère automatiquement un schéma visuel (SVG) de l'EFA/OP dans sa localité,
à partir des données déjà collectées : le siège, les bâtiments d'exploitation,
les éléments du paysage, les parcelles (plan de localisation, en lien avec le
zonage et la mise en valeur), et les activités avec leurs flux entrants/sortants
(schéma général de fonctionnement). Rien n'est ressaisi : tout est dérivé du
diagnostic.

Gestion multi-site : si plusieurs éléments (parcelles, bâtiments, paysage)
indiquent des sites différents, un plan général (vue d'ensemble) et un plan
détaillé par site sont générés séparément — voir list_sites().

Le rendu est un SVG (redimensionnable sans perte, ouvrable dans un navigateur,
Inkscape, ou insérable dans Word/PowerPoint), généré par templating de chaînes
de caractères — aucune dépendance graphique lourde supplémentaire.
"""
import html


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _wrap(text: str, width: int, max_lines: int = 2) -> list:
    """Découpe un texte en lignes d'au plus `width` caractères, tronque à
    `max_lines` lignes avec '...' si le texte est plus long."""
    words = str(text or "").split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and (len(words) > sum(len(l.split()) for l in lines)):
        lines[-1] = lines[-1].rstrip(".")
        if len(lines[-1]) > width - 3:
            lines[-1] = lines[-1][:width - 3]
        lines[-1] += "..."
    return lines or [""]


def _box(x: float, y: float, w: float, h: float, fill: str, stroke: str,
         title_lines: list, subtitle: str = "", dashed: bool = False) -> str:
    dash_attr = ' stroke-dasharray="5,4"' if dashed else ""
    parts = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
             f'rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash_attr}/>']
    text_y = y + 24 if len(title_lines) == 1 else y + 18
    for i, line in enumerate(title_lines):
        parts.append(f'<text x="{x + w / 2:.1f}" y="{text_y + i * 16:.1f}" text-anchor="middle" '
                      f'font-size="12" font-weight="bold" fill="#212121">{_esc(line)}</text>')
    if subtitle:
        sub_y = y + h - 10
        parts.append(f'<text x="{x + w / 2:.1f}" y="{sub_y:.1f}" text-anchor="middle" '
                      f'font-size="9.5" fill="#616161">{_esc(subtitle)}</text>')
    return "".join(parts)


def _arrow_in(x: float, y_center: float, label_lines: list, marker_id: str, length: float = 90) -> str:
    x0 = x - length
    parts = [f'<line x1="{x0:.1f}" y1="{y_center:.1f}" x2="{x - 4:.1f}" y2="{y_center:.1f}" '
             f'stroke="#1565c0" stroke-width="2" marker-end="url(#{marker_id})"/>']
    for i, line in enumerate(label_lines):
        parts.append(f'<text x="{x0:.1f}" y="{y_center - 8 - (len(label_lines) - 1 - i) * 12:.1f}" '
                      f'text-anchor="start" font-size="9" fill="#1565c0">{_esc(line)}</text>')
    return "".join(parts)


def _arrow_out(x: float, y_center: float, label_lines: list, marker_id: str, length: float = 90) -> str:
    x1 = x + length
    parts = [f'<line x1="{x + 4:.1f}" y1="{y_center:.1f}" x2="{x1:.1f}" y2="{y_center:.1f}" '
             f'stroke="#c62828" stroke-width="2" marker-end="url(#{marker_id})"/>']
    for i, line in enumerate(label_lines):
        parts.append(f'<text x="{x1:.1f}" y="{y_center - 8 - (len(label_lines) - 1 - i) * 12:.1f}" '
                      f'text-anchor="end" font-size="9" fill="#c62828">{_esc(line)}</text>')
    return "".join(parts)


def _row_label(x: float, y: float, text: str, color: str) -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="start" font-size="12" '
            f'font-weight="bold" fill="{color}">{_esc(text)}</text>')


def has_enough_data(diagnostic: dict) -> bool:
    ent = diagnostic.get("entreprise", {})
    return bool(ent.get("parcelles")) or bool(ent.get("activites")) or \
        bool(ent.get("batiments")) or bool(ent.get("paysage")) or bool((ent.get("siege") or {}).get("nom"))


def list_sites(diagnostic: dict) -> list:
    """Liste des sites distincts nommés parmi parcelles/bâtiments/paysage/siège.
    Liste vide si l'EFA/OP n'a qu'un seul site (mode simple, pas de champ 'site' renseigné)."""
    ent = diagnostic.get("entreprise", {})
    sites = set()
    for collection_key in ("parcelles", "batiments", "paysage"):
        for item in ent.get(collection_key, []):
            s = (item.get("site") or "").strip()
            if s:
                sites.add(s)
    siege_site = (ent.get("siege", {}).get("site") or "").strip()
    if siege_site:
        sites.add(siege_site)
    return sorted(sites)


def _filter_site(items: list, site) -> list:
    if site is None:
        return items
    return [it for it in items if (it.get("site") or "").strip() == site]


_UNITS_LABELS_FR = {"batiment_usage": {}, }


def generate_site_plan_svg(diagnostic: dict, lang: str = "fr", site=None, include_flux: bool = True) -> str:
    """Génère le plan d'un site (ou de l'ensemble si `site` est None, mode
    mono-site). `include_flux` ajoute la ligne Activités + flux en bas."""
    ent = diagnostic.get("entreprise", {})
    ident = diagnostic.get("identification", {})
    code = diagnostic.get("code", "—")

    parcelles = _filter_site(ent.get("parcelles", []), site)
    batiments = _filter_site(ent.get("batiments", []), site)
    paysage = _filter_site(ent.get("paysage", []), site)
    siege = ent.get("siege", {})
    siege_site = (siege.get("site") or "").strip()
    show_siege = bool(siege.get("nom")) and (site is None or siege_site == site or not siege_site)
    activites = ent.get("activites", []) if include_flux else []

    box_w, box_h, gap = 170, 72, 190
    left_margin, right_margin = 150, 150

    rows = []  # (label, color, items_kind) où items_kind détermine le rendu
    if show_siege:
        rows.append("siege")
    if parcelles:
        rows.append("parcelles")
    if batiments:
        rows.append("batiments")
    if paysage:
        rows.append("paysage")
    if activites:
        rows.append("activites")

    n_cols = max(len(parcelles), len(batiments), len(paysage), len(activites), 1)
    width = left_margin + n_cols * (box_w + gap) - gap + right_margin

    y = 34
    y_title = y
    y += 22
    y_context = y
    y += 46

    row_positions = {}
    for row in rows:
        row_positions[row] = y
        y += box_h + 78

    height = y + 20

    svg = [f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="Helvetica, Arial, sans-serif">']
    svg.append('<defs>'
               '<marker id="arrowIn" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
               '<path d="M0,0 L6,3 L0,6 Z" fill="#1565c0"/></marker>'
               '<marker id="arrowOut" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
               '<path d="M0,0 L6,3 L0,6 Z" fill="#c62828"/></marker>'
               '</defs>')
    svg.append('<rect width="100%" height="100%" fill="#fafafa"/>')

    if lang == "fr":
        title = f"Plan du site « {site} »" if site else "Plan de localisation et flux"
    else:
        title = f"Site plan — '{site}'" if site else "Site plan and flows"
    title += f" — {code}"
    svg.append(f'<text x="{width / 2:.1f}" y="{y_title}" text-anchor="middle" font-size="20" '
               f'font-weight="bold" fill="#1b5e20">{_esc(title)}</text>')

    context_bits = [b for b in [ident.get("village"), ident.get("region"), ident.get("pays")] if b]
    if context_bits:
        svg.append(f'<text x="{width / 2:.1f}" y="{y_context}" text-anchor="middle" font-size="13" '
                   f'fill="#555">{_esc(" — ".join(context_bits))}</text>')

    labels = {
        "siege": ("SIÈGE" if lang == "fr" else "HEADQUARTERS", "#4527a0"),
        "parcelles": ("FONCIER" if lang == "fr" else "LAND", "#2e7d32"),
        "batiments": ("BÂTIMENTS" if lang == "fr" else "BUILDINGS", "#5d4037"),
        "paysage": ("PAYSAGE" if lang == "fr" else "LANDSCAPE", "#00838f"),
        "activites": ("ACTIVITÉS" if lang == "fr" else "ACTIVITIES", "#e65100"),
    }

    if "siege" in row_positions:
        ry = row_positions["siege"]
        label, color = labels["siege"]
        svg.append(_row_label(left_margin, ry - 14, label, color))
        title_lines = _wrap(siege.get("nom") or "-", 18)
        svg.append(_box(left_margin, ry, box_w, box_h, "#ede7f6", "#4527a0", title_lines,
                        (siege.get("description") or "")[:26]))

    if "parcelles" in row_positions:
        ry = row_positions["parcelles"]
        label, color = labels["parcelles"]
        svg.append(_row_label(left_margin, ry - 14, label, color))
        x = left_margin
        for p in parcelles:
            title_lines = _wrap(p.get("nom") or "-", 18)
            mev = p.get("mise_en_valeur", True)
            fill = "#c8e6c9" if mev else "#eeeeee"
            stroke = "#2e7d32" if mev else "#9e9e9e"
            surface = p.get("surface", 0) or 0
            statut = p.get("statut", "")
            zonage = p.get("zonage", "")
            mev_label = "" if mev else (" · non exploitée" if lang == "fr" else " · unused")
            subtitle = f"{zonage + ' · ' if zonage else ''}{surface:g} ha · {statut}{mev_label}"
            svg.append(_box(x, ry, box_w, box_h, fill, stroke, title_lines, subtitle, dashed=not mev))
            x += box_w + gap

    if "batiments" in row_positions:
        ry = row_positions["batiments"]
        label, color = labels["batiments"]
        svg.append(_row_label(left_margin, ry - 14, label, color))
        x = left_margin
        for b in batiments:
            title_lines = _wrap(b.get("type") or "-", 18)
            svg.append(_box(x, ry, box_w, box_h, "#efebe9", "#5d4037", title_lines, b.get("usage", "")))
            x += box_w + gap

    if "paysage" in row_positions:
        ry = row_positions["paysage"]
        label, color = labels["paysage"]
        svg.append(_row_label(left_margin, ry - 14, label, color))
        x = left_margin
        for pa in paysage:
            title_lines = _wrap(pa.get("element") or "-", 18)
            svg.append(_box(x, ry, box_w, box_h, "#e0f7fa", "#00838f", title_lines,
                            (pa.get("utilisation") or "")[:26]))
            x += box_w + gap

    if "activites" in row_positions:
        ry = row_positions["activites"]
        label, color = labels["activites"]
        svg.append(_row_label(left_margin, ry - 14, label, color))
        n_act = len(activites)
        arrow_len = min(90, (gap - 20) / 2) if n_act > 1 else 90
        x = left_margin
        for idx, a in enumerate(activites):
            nom = a.get("nom") or ("Activité" if lang == "fr" else "Activity")
            title_lines = _wrap(nom, 18)
            subtitle = (a.get("quantites_cles") or "")[:24]
            svg.append(_box(x, ry, box_w, box_h, "#fff3e0", "#e65100", title_lines, subtitle))
            fe = (a.get("flux_entrants") or "").strip()
            if fe:
                len_in = 90 if idx == 0 else arrow_len
                svg.append(_arrow_in(x, ry + box_h / 2, _wrap(fe, 20), "arrowIn", len_in))
            fs = (a.get("flux_sortants") or "").strip()
            if fs:
                len_out = 90 if idx == n_act - 1 else arrow_len
                svg.append(_arrow_out(x + box_w, ry + box_h / 2, _wrap(fs, 20), "arrowOut", len_out))
            x += box_w + gap

    if not rows:
        msg = "Aucune donnée à représenter." if lang == "fr" else "No data to display."
        svg.append(f'<text x="{width / 2:.1f}" y="{y_context + 40:.1f}" text-anchor="middle" '
                   f'font-size="13" fill="#9e9e9e" font-style="italic">{_esc(msg)}</text>')

    svg.append('</svg>')
    return "".join(svg)


def generate_general_plan_svg(diagnostic: dict, lang: str = "fr") -> str:
    """Vue d'ensemble simplifiée quand plusieurs sites existent : une boîte
    par site avec un résumé de son contenu (nombre de parcelles/bâtiments)."""
    ent = diagnostic.get("entreprise", {})
    ident = diagnostic.get("identification", {})
    code = diagnostic.get("code", "—")
    sites = list_sites(diagnostic)

    box_w, box_h, gap = 200, 110, 60
    left_margin = 80
    width = left_margin * 2 + len(sites) * (box_w + gap) - gap
    height = 220

    svg = [f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="Helvetica, Arial, sans-serif">']
    svg.append('<rect width="100%" height="100%" fill="#fafafa"/>')

    title = f"Plan général — {code}" if lang == "fr" else f"General plan — {code}"
    svg.append(f'<text x="{width / 2:.1f}" y="34" text-anchor="middle" font-size="20" '
               f'font-weight="bold" fill="#1b5e20">{_esc(title)}</text>')
    context_bits = [b for b in [ident.get("village"), ident.get("region"), ident.get("pays")] if b]
    if context_bits:
        svg.append(f'<text x="{width / 2:.1f}" y="56" text-anchor="middle" font-size="13" '
                   f'fill="#555">{_esc(" — ".join(context_bits))}</text>')

    x = left_margin
    y = 100
    for site in sites:
        n_parcelles = len(_filter_site(ent.get("parcelles", []), site))
        n_batiments = len(_filter_site(ent.get("batiments", []), site))
        n_paysage = len(_filter_site(ent.get("paysage", []), site))
        siege_here = (ent.get("siege", {}).get("site") or "").strip() == site
        subtitle_lines = []
        if siege_here:
            subtitle_lines.append("🏠 " + ("Siège" if lang == "fr" else "HQ"))
        subtitle_lines.append(
            (f"{n_parcelles} parcelle(s) · {n_batiments} bâtiment(s)" if lang == "fr"
             else f"{n_parcelles} plot(s) · {n_batiments} building(s)"))
        subtitle = " — ".join(subtitle_lines)
        svg.append(_box(x, y, box_w, box_h, "#e3f2fd", "#1565c0", _wrap(site, 20), subtitle))
        x += box_w + gap

    svg.append('</svg>')
    return "".join(svg)


# Compatibilité ascendante : ancien point d'entrée utilisé avant la gestion multi-site.
def generate_schema_svg(diagnostic: dict, lang: str = "fr") -> str:
    return generate_site_plan_svg(diagnostic, lang, site=None, include_flux=True)

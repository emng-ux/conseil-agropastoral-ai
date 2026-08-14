"""Import de diagnostics existants au format Excel/CSV, et génération d'un modèle
téléchargeable qui reflète exactement le schéma de l'étoile du conseil."""
import io
import pandas as pd

from modules.collecte import load_schema


def build_template_dataframe(lang: str = "fr") -> pd.DataFrame:
    """Construit un modèle Excel à une ligne, une colonne par champ (branche.champ)."""
    schema = load_schema()["branches"]
    columns = []
    for branch_key, branch in schema.items():
        for field in branch["fields"]:
            if field["type"] == "activity_list":
                columns.append(f"{branch_key}.{field['id']}_1_nom")
                columns.append(f"{branch_key}.{field['id']}_1_part_marche")
                columns.append(f"{branch_key}.{field['id']}_1_croissance")
            else:
                columns.append(f"{branch_key}.{field['id']}")
    df = pd.DataFrame(columns=["nom", "type", "conseiller"] + columns)
    return df


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="diagnostic")
    return buffer.getvalue()


def import_file_to_diagnostic(uploaded_file) -> dict:
    """Lit un fichier Excel ou CSV suivant le modèle et retourne un diagnostic structuré.
    Lève une exception si le fichier est illisible ou vide."""
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    if df.empty:
        raise ValueError("Fichier vide")

    row = df.iloc[0].to_dict()
    diagnostic = {
        "nom": str(row.pop("nom", "") or ""),
        "type": str(row.pop("type", "") or ""),
        "conseiller": str(row.pop("conseiller", "") or ""),
        "etoile": {},
    }

    schema = load_schema()["branches"]
    for branch_key, branch in schema.items():
        branch_data = {}
        for field in branch["fields"]:
            fid = field["id"]
            if field["type"] == "activity_list":
                col_nom = f"{branch_key}.{fid}_1_nom"
                col_pm = f"{branch_key}.{fid}_1_part_marche"
                col_tc = f"{branch_key}.{fid}_1_croissance"
                if col_nom in row and pd.notna(row[col_nom]) and str(row[col_nom]).strip():
                    branch_data[fid] = [{
                        "nom": str(row[col_nom]),
                        "part_marche_relative": float(row.get(col_pm, 1.0) or 1.0),
                        "taux_croissance": float(row.get(col_tc, 0.0) or 0.0),
                    }]
                else:
                    branch_data[fid] = []
            else:
                col = f"{branch_key}.{fid}"
                value = row.get(col, "")
                if pd.isna(value):
                    value = "" if field["type"] != "number" else 0.0
                if field["type"] == "number":
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = 0.0
                branch_data[fid] = value
        diagnostic["etoile"][branch_key] = branch_data

    return diagnostic

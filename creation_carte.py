import pandas as pd
import folium
import html
import json

# ---------- Paramètres ----------
CSV_PATH = "labellisation.csv"
SEP = ";"

# ---------- Lecture & nettoyage ----------
df = pd.read_csv(CSV_PATH, sep=SEP, dtype=str).fillna("")
df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
df = df.dropna(subset=["Latitude", "Longitude"])
df = df[df["Label"].str.strip() != ""]            # n'afficher que les lignes avec Label non vide
df["Type_e"] = df["Type_e"].str.strip().str.lower()
df["Label"] = df["Label"].str.strip()
df["Secteur"] = df["Secteur"].str.strip().str.lower()

# ---------- Couleurs ----------
couleurs_type = {
    "école": "seagreen",
    "collège": "crimson",
    "lycée gt ou polyvalent": "purple",
    "lycée professionnel": "darkblue",
    "territoire": "DeepSkyBlue",
    "autre": "orange"
}

# ---------- Formes ----------
formes_label = {
    "Niveau 1": "triangle",
    "Niveau 2": "circle",
    "Niveau 3": "star"
}

# ---------- Fonctions utilitaires SVG ----------
def svg_icon(shape, color, size=30, stroke="black"):
    s = int(size)
    half = s/2
    stroke_width = max(1, s//12)
    if shape == "circle":
        svg = f'''<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">
            <circle cx="{half}" cy="{half}" r="{half-2}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"/>
        </svg>'''
    elif shape == "rectangle":
        pad = 3
        svg = f'''<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">
            <rect x="{pad}" y="{pad}" width="{s-2*pad}" height="{s-2*pad}" rx="4" ry="4" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"/>
        </svg>'''
    elif shape == "triangle":
        svg = f'''<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">
            <polygon points="{half},3 {s-3},{s-3} 3,{s-3}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"/>
        </svg>'''
    elif shape == "star":
        svg = f'''<svg width="{s}" height="{s}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 .587l3.668 7.431L23.6 9.75l-5.8 5.65L19.335 24 12 19.77 4.665 24l1.535-8.6L.4 9.75l7.932-1.732z" 
                transform="scale({s/24})" fill="{color}" stroke="{stroke}" stroke-width="0.8"/>
        </svg>'''
    else:  # pin
        svg = f'''<svg width="{s}" height="{s}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.14 2 5 5.14 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.86-3.14-7-7-7z" 
                transform="scale({s/24})" fill="{color}" stroke="{stroke}" stroke-width="0.6"/>
            <circle cx="12" cy="9" r="2.5" transform="scale({s/24})" fill="white"/>
        </svg>'''
    return svg

#--- Construction conditionnelle du popup ---
def li_if_not_empty(row, fieldname):
    value = row.get(fieldname, "")
    return f"<li>{html.escape(value)}</li>" if value else ""

def territoire(row, fieldname):
    value = row.get(fieldname, "")
    if value[:5] == "terri":
        df_t = df[df["territoire"]==value]
        etabs = "<h3>Écoles et établissements du territoire</h3><ul>"
        for etab in df_t['Appellation officielle']:
            etabs = etabs + "<li>" + etab + "</li>"
        etabs = etabs + "</ul>"
        op = f"{etabs}"
    else:
        op = f"UAI : {html.escape(row.get('Num_etab',''))}<br />"
    return op
    
# ---------- Carte ----------
m = folium.Map(location=[47.2, 6.1], zoom_start=8, tiles="OpenStreetMap")
layer_groups = {}
ICON_SIZE = 24

for _, row in df.iterrows():
    t, l, s = row["Type_e"], row["Label"], row["Secteur"]
    couleur = couleurs_type.get(t, "orange")
    forme = formes_label.get(l, "pin")

    popup_html = (
        f"<h1>{html.escape(row.get('Appellation officielle',''))}</h1>"
        f"<p>"
        f"{territoire(row, 'Num_etab')}"
        f"Type : {html.escape(row.get('Nature uai','').lower())} {html.escape(row.get('Secteur','').lower())}<br />"
        f"Commune : {html.escape(row.get('Commune',''))}</p>"
        f"<h3>Label : {html.escape(l)} ({html.escape(row.get('Année',''))})</h3>"
        f"<p>Historique :</p>"
        f"<ul><li>1<sup>re</sup> labellisation : {html.escape(row.get('Date de 1ère labellisation',''))}</li>"
        f"<li>{html.escape(row.get('Renouvellement 1',''))}</li>"
        f"{li_if_not_empty(row, 'Renouvellement 2')}"
        f"{li_if_not_empty(row, 'Renouvellement 3')}"
        f"{li_if_not_empty(row, 'Renouvellement 4')}"
        f"</ul>"
    )

    svg = svg_icon(forme, couleur, size=ICON_SIZE)
    div_html = f"""<div style="width:{ICON_SIZE}px; height:{ICON_SIZE}px; transform: translate(-50%, -50%);">{svg}</div>"""
    icon = folium.DivIcon(html=div_html)

    marker = folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=folium.Popup(popup_html, max_width=500),
        tooltip=row.get("Appellation officielle", ""),
        icon=icon
    )

    key = (t, l, s)
    if key not in layer_groups:
        fg = folium.FeatureGroup(name=f"{t} | {l} | {s}", show=True)
        layer_groups[key] = fg
        m.add_child(fg)

    marker.add_to(layer_groups[key])

# ---------- Légende ----------
legend_types = "".join(
    f'<div style="margin:4px 0;"><span style="display:inline-block;width:18px;height:12px;background:{col};margin-right:8px;border:1px solid #333;"></span>{html.escape(k)}</div>'
    for k, col in couleurs_type.items()
)
legend_labels = "".join(
    f'<div style="margin:4px 0;">{svg_icon(shape, "black", size=16)} {html.escape(lbl)}</div>'
    for lbl, shape in formes_label.items()
)
legend_html = f"""
<div style="position: fixed; bottom: 30px; left: 30px; width: 200px;
    background-color: white; border:2px solid grey; border-radius:8px; padding: 8px;
    font-size: 13px; z-index:9999; box-shadow: 0 2px 6px rgba(0,0,0,0.25);">
<b>Légende</b><hr style="margin-top:8px;margin-bottom:0">
<b>Couleurs (Type)</b><br>{legend_types}
<hr style="margin-top:8px;margin-bottom:0"><b>Formes (Label)</b><br>{legend_labels}
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ---------- Panneau filtres ----------
types = sorted(df["Type_e"].unique())
labels = sorted(df["Label"].unique())
secteurs = sorted(df["Secteur"].unique())

types_html = "".join(f'<label><input type="checkbox" class="typeFilter" value="{t}" checked> {t}</label><br>' for t in types)
labels_html = "".join(f'<label><input type="checkbox" class="labelFilter" value="{l}" checked> {l}</label><br>' for l in labels)
secteurs_html = "".join(f'<label><input type="checkbox" class="secteurFilter" value="{s}" checked> {s}</label><br>' for s in secteurs)

group_names = {f"{k[0]}|{k[1]}|{k[2]}": fg.get_name() for k, fg in layer_groups.items()}
group_names_json = json.dumps(group_names)
map_js_name = json.dumps(m.get_name())

filter_div = f"""
<div id="filter-pane" style="position: fixed; top: 18px; right: 18px; width: 180px;
    background-color: white; border:2px solid grey; border-radius:8px; padding: 8px;
    font-size: 13px; z-index:9999; box-shadow: 0 2px 6px rgba(0,0,0,0.25); max-height: 460px; overflow: auto;">
<b>Filtres</b><hr style="margin-top:8px;margin-bottom:0">
<button id="toggle-types">Types ▲</button>
<div id="types-section" style="margin-top:6px;">{types_html}</div><hr style="margin-top:8px;margin-bottom:0">
<button id="toggle-labels">Labels ▲</button>
<div id="labels-section" style="margin-top:6px;">{labels_html}</div><hr style="margin-top:8px;margin-bottom:0">
<button id="toggle-secteurs">Secteurs ▲</button>
<div id="secteurs-section" style="margin-top:6px;">{secteurs_html}</div>
</div>

<script>
var groupNames = {group_names_json};
document.addEventListener('DOMContentLoaded', function() {{
    // Référence à la map Folium
    var map = window[{map_js_name}];

    // Résolution des FeatureGroups créés côté Python
    var allGroups = {{}};
    for (var key in groupNames) {{
        var varName = groupNames[key];
        allGroups[key] = window[varName];
        if (!allGroups[key]) console.warn("Groupe non trouvé:", key, varName);
    }}

    // Empêcher la carte d'interpréter les clics dans le panneau
    var pane = document.getElementById('filter-pane');
    if (pane && typeof L !== "undefined" && L.DomEvent) {{
        L.DomEvent.disableClickPropagation(pane);
    }}

    // Fonction utilitaire pour mettre en place les toggles accordéon
    function setupToggle(btnId, sectionId, title) {{
        var btn = document.getElementById(btnId);
        var sec = document.getElementById(sectionId);
        if (!btn || !sec) return;
        // état initial : affiché -> bouton montre ▲
        sec.style.display = 'block';
        btn.innerText = title + " ▲";
        btn.addEventListener('click', function() {{
            if (sec.style.display === 'none') {{
                sec.style.display = 'block';
                btn.innerText = title + " ▲";
            }} else {{
                sec.style.display = 'none';
                btn.innerText = title + " ▼";
            }}
        }});
    }}

    // Installer les 3 accordéons
    setupToggle('toggle-types', 'types-section', 'Types');
    setupToggle('toggle-labels', 'labels-section', 'Labels');
    setupToggle('toggle-secteurs', 'secteurs-section', 'Secteurs');

    // Fonction de filtrage (même logique que précédemment)
    function applyFilters() {{
        var checkedTypes = Array.from(document.querySelectorAll('.typeFilter:checked')).map(cb => cb.value);
        var checkedLabels = Array.from(document.querySelectorAll('.labelFilter:checked')).map(cb => cb.value);
        var checkedSecteurs = Array.from(document.querySelectorAll('.secteurFilter:checked')).map(cb => cb.value);
        var allowTypes = checkedTypes.length === 0;
        var allowLabels = checkedLabels.length === 0;
        var allowSecteurs = checkedSecteurs.length === 0;

        for (var key in allGroups) {{
            var parts = key.split('|');
            var type = parts[0];
            var label = parts[1];
            var secteur = parts[2];
            var show = (allowTypes || checkedTypes.indexOf(type) !== -1)
                    && (allowLabels || checkedLabels.indexOf(label) !== -1)
                    && (allowSecteurs || checkedSecteurs.indexOf(secteur) !== -1);
            var layer = allGroups[key];
            if (!layer) continue;
            if (show) {{
                if (!map.hasLayer(layer)) map.addLayer(layer);
            }} else {{
                if (map.hasLayer(layer)) map.removeLayer(layer);
            }}
        }}
    }}

    // Attacher les écouteurs sur les checkboxes
    document.querySelectorAll('.typeFilter, .labelFilter, .secteurFilter').forEach(cb => cb.addEventListener('change', applyFilters));

    // état initial
    applyFilters();
}});
</script>
"""

for dsden in [25,39,70,90]:
    fichier = "json/dpt"+str(dsden)+".json"
    folium.GeoJson(
        fichier,
        control=True,
        style_function=lambda feature: {
            "color": "black",
            "fillColor": "white",
            "weight": 1,
            "fillOpacity": 0.10,
        }
    ).add_to(m)

m.get_root().html.add_child(folium.Element(filter_div))

# ---------- Sauvegarde ----------
OUT = "carte_etablissements.html"
m.save(OUT)
print("Carte générée :", OUT)
import os
import subprocess
from datetime import datetime

# --- paramètres à adapter ---
REPO_PATH = r"C:\Users\claudelg\Nextcloud\GT EDD\Labellisations\cartes"  # dossier local du dépôt
FICHIER_HTML = "carte_etablissements.html"  # le fichier généré
MESSAGE = f"Mise à jour automatique de la carte ({datetime.now():%Y-%m-%d %H:%M})"

def git_push(repo_path, message, fichier):
    os.chdir(repo_path)
    print(f"📂 Répertoire actuel : {os.getcwd()}")
    
    # Vérifie que le fichier existe
    if not os.path.exists(os.path.join(repo_path, fichier)):
        raise FileNotFoundError(f"Le fichier {fichier} est introuvable dans {repo_path}")
    
    # Exécute les commandes git
    subprocess.run(["git", "add", fichier], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    print("🚀 Fichier envoyé sur GitHub avec succès.")

if __name__ == "__main__":
    git_push(REPO_PATH, MESSAGE, FICHIER_HTML)
#!/bin/bash
echo "[+] Déploiement en cours..."

#vider le cache
echo "[+] vider le cache pip.."

# Installer les dépendances
echo "[+] Installation des dépendances..."
pip install setuptools
pip install -r requirements.txt

# Appliquer les migrations
echo "[+] Application des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers static
echo "[+] Collecte des fichiers static..."
python manage.py collectstatic --noinput --clear

echo "✅ Déploiement terminé!"
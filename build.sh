#!/bin/bash
echo "[+]============== Déploiement en cours..."

# Installer les dépendances
echo "[+]============== Installation des dépendances..."
python3.12 -m pip install -r requirements.txt

echo "[+]============== Application des migrations..."
python3.12 manage.py makemigrations --noinput

# Appliquer les migrations
echo "[+]============== Application des migrations..."
python3.12 manage.py migrate --noinput

# Collecter les fichiers static
echo "[+]============= Collecte des fichiers static..."
python3.12 manage.py collectstatic --noinput --clear

echo "✅ Déploiement terminé!"
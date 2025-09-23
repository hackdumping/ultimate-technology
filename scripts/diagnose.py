# scripts/diagnose.py
import os
import sys
import django

# Ajouter le chemin du projet au Python path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UltimateTechnology.settings')
django.setup()

from django.conf import settings
import cloudinary
from cloudinary import uploader


def diagnose_cloudinary():
    print("=== DIAGNOSTIC CLOUDINARY ===")

    # 1. Vérifier la configuration
    if not hasattr(settings, 'CLOUDINARY_STORAGE'):
        print("❌ CLOUDINARY_STORAGE non configuré dans settings.py")
        return False

    config = settings.CLOUDINARY_STORAGE
    print(f"✓ Cloud Name: {config.get('CLOUD_NAME', 'NON DÉFINI')}")
    print(f"✓ API Key: {config.get('API_KEY', 'NON DÉFINI')}")
    print(f"✓ API Secret: {'*' * len(config.get('API_SECRET', '')) if config.get('API_SECRET') else 'NON DÉFINI'}")

    # 2. Configurer Cloudinary
    try:
        cloudinary.config(
            cloud_name=config['CLOUD_NAME'],
            api_key=config['API_KEY'],
            api_secret=config['API_SECRET'],
            secure=True
        )
        print("✓ Configuration Cloudinary appliquée")
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False

    # 3. Test de connexion
    try:
        result = uploader.upload(
            "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            folder="test_connexion"
        )
        print("✅ Connexion Cloudinary réussie!")
        print(f"📁 Test upload ID: {result['public_id']}")
        return True
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False


def check_media_folder():
    print("\n=== VÉRIFICATION DOSSIER MEDIA ===")
    media_path = settings.MEDIA_ROOT
    print(f"📁 Chemin media: {media_path}")

    if not os.path.exists(media_path):
        print("❌ Le dossier media n'existe pas")
        return False

    # Compter les fichiers
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    image_files = []

    for root, dirs, files in os.walk(media_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                image_files.append(os.path.join(root, file))

    print(f"📊 {len(image_files)} fichiers image trouvés")

    # Afficher les 5 premiers fichiers
    for i, file_path in enumerate(image_files[:5]):
        print(f"  {i + 1}. {os.path.basename(file_path)}")

    if len(image_files) > 5:
        print(f"  ... et {len(image_files) - 5} autres fichiers")

    return True


if __name__ == "__main__":
    print("🔍 Lancement du diagnostic...")

    cloudinary_ok = diagnose_cloudinary()
    media_ok = check_media_folder()

    if cloudinary_ok and media_ok:
        print("\n🎉 Diagnostic réussi! Vous pouvez lancer la migration.")
    else:
        print("\n❌ Des problèmes ont été détectés. Corrigez-les avant de migrer.")
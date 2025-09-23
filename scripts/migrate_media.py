# scripts/migrate_media.py
import os
import sys
import django
import time
from pathlib import Path

# Configuration du chemin
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UltimateTechnology.settings')
django.setup()

from django.conf import settings
import cloudinary
from cloudinary import uploader

# Configuration Cloudinary
config = settings.CLOUDINARY_STORAGE
cloudinary.config(
    cloud_name=config['CLOUD_NAME'],
    api_key=config['API_KEY'],
    api_secret=config['API_SECRET'],
    secure=True
)


def migrate_media_to_cloudinary():
    print("🚀 DÉBUT DE LA MIGRATION CLOUDINARY")
    print("=" * 50)

    media_root = Path(settings.MEDIA_ROOT)

    if not media_root.exists():
        print(f"❌ Le dossier media n'existe pas: {media_root}")
        return

    # Trouver tous les fichiers image
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    image_files = []

    for ext in image_extensions:
        image_files.extend(media_root.rglob(f'*{ext}'))
        image_files.extend(media_root.rglob(f'*{ext.upper()}'))

    print(f"📁 Dossier media: {media_root}")
    print(f"📊 {len(image_files)} fichiers à migrer")
    print("=" * 50)

    migrated_files = []
    errors = []

    for i, file_path in enumerate(image_files, 1):
        relative_path = file_path.relative_to(media_root)
        cloudinary_folder = str(relative_path.parent) if relative_path.parent != Path('.') else None

        print(f"\n[{i}/{len(image_files)}] 🔄 Traitement de: {relative_path}")

        try:
            # Upload vers Cloudinary
            result = uploader.upload(
                str(file_path),
                folder=cloudinary_folder,
                use_filename=True,
                unique_filename=False,
                resource_type="image"
            )

            migrated_files.append({
                'local_path': str(file_path),
                'cloudinary_url': result['secure_url'],
                'public_id': result['public_id']
            })

            print(f"✅ SUCCÈS: {result['public_id']}")

        except Exception as e:
            errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            print(f"❌ ERREUR: {e}")

        # Pause courte pour éviter les limitations d'API
        time.sleep(0.5)

    # Générer le rapport
    print("\n" + "=" * 50)
    print("📊 RAPPORT FINAL DE MIGRATION")
    print("=" * 50)
    print(f"✅ Fichiers migrés: {len(migrated_files)}")
    print(f"❌ Erreurs: {len(errors)}")

    if migrated_files:
        print("\n📁 FICHIERS MIGRÉS AVEC SUCCÈS:")
        for file in migrated_files[:10]:  # Afficher les 10 premiers
            print(f"  ✓ {file['public_id']}")
        if len(migrated_files) > 10:
            print(f"  ... et {len(migrated_files) - 10} autres")

    if errors:
        print("\n❌ FICHIERS EN ERREUR:")
        for error in errors:
            print(f"  ✗ {os.path.basename(error['file'])}: {error['error']}")

    # Sauvegarder le log
    save_migration_log(migrated_files, errors)

    return migrated_files, errors


def save_migration_log(migrated_files, errors):
    """Sauvegarde un log de la migration"""
    import json
    from datetime import datetime

    log_data = {
        'timestamp': datetime.now().isoformat(),
        'migrated_files': migrated_files,
        'errors': errors
    }

    log_file = project_path + '/cloudinary_migration_log.json'

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 Log sauvegardé: {log_file}")


if __name__ == "__main__":
    migrate_media_to_cloudinary()
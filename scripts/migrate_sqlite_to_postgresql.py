# scripts/migrate_to_supabase_simple.py
import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UltimateTechnology.settings')
django.setup()


def migrate_to_supabase():
    print("🚀 MIGRATION VERS SUPABASE")
    print("=" * 40)

    # 1. Test connexion Supabase
    print("1. 🔗 Test connexion Supabase...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
        print("✅ Connexion Supabase OK")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return

    # 2. Créer les tables avec les migrations
    print("2. 🏗️  Création des tables...")
    call_command('migrate')

    # 3. Exporter les données SQLite
    print("3. 📤 Export données SQLite...")
    call_command('dumpdata',
                 output='supabase_migration.json',
                 indent=2,
                 use_natural_foreign_keys=True,
                 use_natural_primary_keys=True)

    # 4. Importer dans Supabase
    print("4. 📥 Import vers Supabase...")
    call_command('loaddata', 'supabase_migration.json')

    print("🎉 MIGRATION TERMINÉE!")
    print("🌐 Vos données sont maintenant sur Supabase!")


if __name__ == "__main__":
    migrate_to_supabase()
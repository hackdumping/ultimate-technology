# scripts/fix_supabase.py
import os
import django
import psycopg2

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UltimateTechnology.settings')
django.setup()

from django.conf import settings


def fix_supabase_permissions():
    print("🔧 RÉPARATION DES PERMISSIONS SUPABASE")
    print("=" * 50)

    db_config = settings.DATABASES['default']

    try:
        conn = psycopg2.connect(
            dbname=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT']
        )

        with conn.cursor() as cursor:
            # Donner toutes les permissions
            queries = [
                "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;",
                "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;",
                "GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;",
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;",
            ]

            for query in queries:
                cursor.execute(query)
                print(f"✅ Exécuté: {query.split('TO')[0]}...")

        conn.commit()
        conn.close()
        print("🎉 Permissions réparées avec succès!")

    except Exception as e:
        print(f"❌ Erreur: {e}")


def recreate_django_tables():
    print("\n🔄 RECRÉATION DES TABLES DJANGO")
    print("=" * 50)

    # Commande pour recréer les tables
    os.system("python manage.py flush --noinput")
    os.system("python manage.py makemigrations")
    os.system("python manage.py migrate")

    print("✅ Tables Django recréées!")


if __name__ == "__main__":
    fix_supabase_permissions()
    recreate_django_tables()
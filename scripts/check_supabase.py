import os
import django
import psycopg2

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UltimateTechnology.settings')
django.setup()

from django.conf import settings


def check_supabase_connection():
    print("🔗 VÉRIFICATION CONNEXION SUPABASE")
    print("=" * 40)

    # Afficher la configuration (masquer le mot de passe)
    db_config = settings.DATABASES['default']
    print(f"🏷️  Environnement: {'PRODUCTION' if not settings.DEBUG else 'DÉVELOPPEMENT'}")
    print(f"📊 Base de données: {db_config['NAME']}")
    print(f"👤 Utilisateur: {db_config['USER']}")
    print(f"🌐 Hôte: {db_config['HOST']}")
    print(f"🔒 Mot de passe: {'*' * len(db_config['PASSWORD']) if db_config['PASSWORD'] else 'NON DÉFINI'}")

    # Tester la connexion
    try:
        conn = psycopg2.connect(
            dbname=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT']
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connexion réussie: {version}")

        # Tester les tables Django
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tables trouvées: {len(tables)}")
            for table in tables:
                print(f"   - {table}")

        conn.close()

    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")


if __name__ == "__main__":
    check_supabase_connection()
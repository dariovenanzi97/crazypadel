import os
import django
import sys

# Configura l'ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crazypadel.settings')
django.setup()

from django.db import connection

def update_user_emails_raw():
    print("Aggiornamento email degli utenti tramite SQL diretto...")
    
    with connection.cursor() as cursor:
        # Conta gli utenti
        cursor.execute("SELECT COUNT(*) FROM accounts_user")
        users_count = cursor.fetchone()[0]
        print(f"Totale utenti: {users_count}")
        
        # Conta utenti senza email
        cursor.execute("SELECT COUNT(*) FROM accounts_user WHERE email IS NULL OR email = ''")
        empty_emails_count = cursor.fetchone()[0]
        print(f"Utenti senza email: {empty_emails_count}")
        
        # Aggiorna le email vuote o nulle
        cursor.execute("""
            UPDATE accounts_user 
            SET email = 'user_' || id || '@example.com' 
            WHERE email IS NULL OR email = ''
        """)
        print(f"Email aggiornate: {cursor.rowcount}")
        
        # Identifica email duplicate
        cursor.execute("""
            SELECT email, COUNT(*) as count 
            FROM accounts_user 
            GROUP BY email 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        print(f"Email duplicate trovate: {len(duplicates)}")
        
        # Risolvi email duplicate
        for email, count in duplicates:
            print(f"Risolvo {count} utenti con email {email}")
            
            # Ottieni gli ID degli utenti con questa email
            cursor.execute("SELECT id FROM accounts_user WHERE email = %s ORDER BY id", [email])
            user_ids = [row[0] for row in cursor.fetchall()]
            
            # Salta il primo utente (mantenendo la sua email), aggiorna gli altri
            for i, user_id in enumerate(user_ids[1:], 1):
                new_email = f"{email.split('@')[0]}_{i}@{email.split('@')[1]}"
                cursor.execute("UPDATE accounts_user SET email = %s WHERE id = %s", [new_email, user_id])
                print(f"Aggiornata email per utente ID {user_id}: {new_email}")
    
    print("Aggiornamento email completato!")

if __name__ == "__main__":
    update_user_emails_raw()
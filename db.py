from datetime import datetime
from flask import Flask
import mysql.connector
from werkzeug.security import generate_password_hash
from user import User
import mysql.connector
from contextlib import closing


mydb = mysql.connector.connect(
  host="localhost",
   user="root",
  password="dogukan1903"
)

mycursor = mydb.cursor()
mycursor.execute("USE ChatDB")

""""""
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        created_by VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS room_members (
    room_id INT,
    username VARCHAR(255) NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    added_by VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_room_admin BOOLEAN,
    PRIMARY KEY (room_id, username),  
    FOREIGN KEY (room_id) REFERENCES rooms(id)    
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        room_id INT NOT NULL,
        text TEXT NOT NULL,
        sender VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")


def save_user(username, email, password):
    
    try:
        # girilen şifreyi hashle
        pasword_hash = generate_password_hash(password)

        # Kullanıcıyı veritabanına ekle
        mycursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, pasword_hash))

        mydb.commit()
    except mysql.connector.IntegrityError as e:
        if e.errno==1062:
             raise ValueError("Bu kullanıcı adı veya e-posta adresi zaten kullanılıyor.")
        else:
            raise e
    
def get_user(email):
    user = None
    try:
        with closing(mydb.cursor()) as mycursor:
            mycursor.execute("""
                SELECT id, username, email, password FROM users
                WHERE email = %s
            """, (email,))
            
            user_data = mycursor.fetchone()
            
            
            if user_data:
                
                user_id, username, email, password_hash = user_data
                
    
                
                user = User(username, email, password_hash)
                
                mycursor.clear_attributes()
    
                return User(username, email, password_hash)
    except Exception as e:
        print(f"HATA ? ? ******** =  {e}")
    return None

def save_room(room_name,created_by):
    
    room_id = None
    
    try:
        # Kullanıcı kontrolü
        user = get_user(created_by)
        if not user:
            raise ValueError("Kullanıcı bulunamadı veya geçersiz.")

        # Odayı veritabanına ekle
        created_at = datetime.now() #anlık zamanı alıyor 
        mycursor.execute("""
            INSERT INTO rooms (name, created_by, created_at)
            VALUES (%s, %s, %s)
        """, (room_name, created_by, created_at))
        
        mycursor.execute("SELECT LAST_INSERT_ID()") #en son  eklenen id yi alır
        room_id = mycursor.fetchone()[0] #satırın sonucunda dönen veriyi alır ve o verinin 0. indeksini yani idsini alır
        mydb.commit()
    except Exception as e:
        print(f"HATA ? ? ******** = {e}")
    
    add_room_member(room_id, room_name, created_by, created_by, is_room_admin=True) #ilk olarak odaya admin eklenir 
                                                                                    #ve admin değeri true olur.
    return room_id
        
def update_room(room_id, room_name):
    try:
        # Odanın adını güncelle
        mycursor.execute("""
            UPDATE rooms
            SET name = %s
            WHERE id = %s
        """, (room_name, room_id))

        # Odaya ait üyelerin odanın adını güncelle
        mycursor.execute("""
            UPDATE room_members
            SET room_name = %s
            WHERE room_id = %s
        """, (room_name, room_id))

        mydb.commit()
        print(f"Room {room_id} updated successfully.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def get_room(room_id):
    try:
        mycursor.execute("""
            SELECT * FROM rooms
            WHERE id = %s
        """, (room_id,))

        room_data = mycursor.fetchone()

        if room_data:
            room_id, name, created_by, created_at = room_data
            print(f"Oda Bulundu: id={room_id}, name={name}, created_by={created_by}, created_at={created_at}")
            return room_data
        else:
            print("Room not found.")
            return None
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return None

def add_room_member(room_id, room_name, username, added_by, is_room_admin=False):
    try:
        # Oda üyesini eklemek için INSERT sorgusu
        added_at = datetime.now()
        mycursor.execute("""
            INSERT INTO room_members (room_id, username, room_name, added_by, added_at, is_room_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (room_id, username, room_name, added_by, added_at, is_room_admin))

        # Veritabanındaki değişiklikleri kaydetme
        mydb.commit()

        print("Oda üyesi başarıyla eklendi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def add_room_members(room_id, room_name, usernames, added_by):
    try:
        # Oda üyelerini eklemek için INSERT sorgusu
        added_at = datetime.now()
        is_room_admin = False

        insert_query = """
            INSERT INTO room_members (room_id, username, room_name, added_by, added_at, is_room_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Her kullanıcı için INSERT işlemi gerçekleştir
        for username in usernames:
            mycursor.execute(insert_query, (room_id, username, room_name, added_by, added_at, is_room_admin))

        # Veritabanındaki değişiklikleri kaydetme
        mydb.commit()

        print("Oda üyeleri başarıyla eklendi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def remove_room_members(room_id, usernames):
    try:
        print("SİLME İŞLEMİ")
        delet_query = """
            DELETE FROM room_members
            WHERE room_id = %s AND username = %s
         """
        for username in usernames:
            mycursor.execute(delet_query, (room_id, username))

        mydb.commit()
        print(f"Room members removed successfully.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")


def edit_room_members(room_id):
    try:
        mycursor.execute("""
            SELECT * FROM room_members
            WHERE room_id = %s
        """, (room_id,))

        room_members_data = mycursor.fetchall()
        
        emails = []
        
        for uye in room_members_data:
            email = uye[1]  # E-posta adresi, tuple'ın ikinci elemanıdır
            emails.append(email)
            
        print("emailler = = == ",emails)
        
        
        room_members_data.clear()
        for mail in emails:
            room_members_data.append(mail)
 
        print("Room_members data = ",room_members_data)
        if room_members_data:
            print(f"Room members found for room_id={room_id}")
            return room_members_data
        else:
            print("No room members found.")
            return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []

def get_room_members(room_id):
    try:
    
        mycursor.execute("""
            SELECT * FROM room_members
            WHERE room_id = %s
        """, (room_id,))

        room_members_data = mycursor.fetchall()
        
        emails = []
        
        for uye in room_members_data:
            email = uye[1]  # E-posta adresi tupleın ikinci elemanıdır
            emails.append(email) #emaile aktarılan değeri emails arrayine eklenir
            
        #print("emailler = = == ",emails)
        
        
        room_members_data.clear() #roommembers_data arreyini temizliyoruz çünkü sadece kullanıcı adlarını ekleiyicez
        for mail in emails: 
            user = get_user(mail) #tutulan email adreslerinin hangi kullanıcı adına sahip olduğunu buluyoruz
            
            if user:
                room_members_data.append(user.username) #bulunan kullanıcı adı room_members_dataya eklenir
                print(room_members_data)
            else:
                print(f"Kullanıcı bulunamadı: {mail}")  #get_user none döndüyse kullanıcı bulunamadı yazdırırız
            
                
        
        print("Room_members data = ",room_members_data)
        if room_members_data:
            print(f"Room members found for room_id={room_id}")
            return room_members_data #kullanıcıları döndürür liste halinde
        else:
            print("No room members found.")
            return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []

def get_rooms_for_user(username):
    try:
        user=get_user(username)
        username=user.email
        print(username)
        
        mycursor.execute("""
            SELECT * FROM room_members
            WHERE username = %s
        """, (username,))

        user_rooms_data = mycursor.fetchall()
        if user_rooms_data:
            print(f"Rooms found for user {username}")
            return user_rooms_data
        else:
            print(f"No rooms found for user {username}")
            return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []

def is_room_member(room_id, username):
    try:
        
        username_=get_user(username)
        username=username_.email
        
        mycursor.execute("""
                SELECT COUNT(*) FROM room_members
                WHERE room_id = %s AND username = %s
        """, (room_id, username))

        count = mycursor.fetchone()[0]

        if count > 0:
            print(f"{username} is a member of room_id={room_id}")
            return True
        else:
            print(f"{username} is not a member of room_id={room_id}")
            return False
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return False

def is_room_admin(room_id, username):
    try:
        username_=get_user(username)
        username=username_.email
        
        mycursor.execute("""
            SELECT COUNT(*) FROM room_members
            WHERE room_id = %s AND username = %s AND is_room_admin = 1
        """, (room_id, username))

        count = mycursor.fetchone()[0]

        if count > 0:
            print(f"{username} is an admin of room_id={room_id}")
            return True
        else:
            print(f"{username} is not an admin of room_id={room_id}")
            return False
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return False

def save_message(room_id,text,sender):
    try:
        date_tame=datetime.now()
        insert_query = """
            INSERT INTO messages (room_id, text, sender,created_at)
            VALUES (%s, %s, %s,%s)
        """
        mycursor.execute(insert_query,(room_id,text,sender,date_tame))
        
        mydb.commit()
        print("mesaj yüklendi")
    except mysql.connector.Error as e:
        print(f"HATA: {e}")

message_fetch_limit=3 # Sayfa başına gösterilecek mesaj sayısı

def get_message(room_id,page=0):
    try: 
        offset = page * message_fetch_limit

        with closing(mydb.cursor()) as mycursor:
            # # mycursor.execute("""
                # SELECT * FROM messages
                # WHERE room_id = %s
                # ORDER BY created_at DESC
                # LIMIT %s OFFSET %s
            # """, (room_id, message_fetch_limit, offset))
            
            mycursor.execute("""
                SELECT * FROM messages
                WHERE room_id = %s
                ORDER BY created_at DESC
                
            """, (room_id,))
            


            messages_data = mycursor.fetchall()

            if messages_data:
                print(f"Mesaj bulundu, Oda={room_id}")
                messages_data = [list(message) for message in messages_data]

                for message in messages_data:
                    message[4] = message[4].strftime("%d %b, %H:%M")
                    
                

                return messages_data[::-1]
            else:
                print(f"Mesaj Bulunamadı, Oda={room_id}")
                return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []
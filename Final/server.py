from datetime import datetime
from flask import Flask, render_template, redirect, url_for,request,redirect,url_for,session
from flask_login import LoginManager,login_required, login_user, logout_user,current_user
from db import add_room_members, edit_room_members, get_message, get_room, get_room_members, get_rooms_for_user, get_user, is_room_admin, is_room_member, remove_room_members, save_message, save_room, save_user, update_room
from user import User
from flask_session import Session
from flask_socketio import SocketIO,send,join_room,leave_room,send,emit

app=Flask(__name__)
app.secret_key = "my secret key"
app.config['SECRET']="123456"
socketio=SocketIO(app, cors_allowed_origins="*") 
login_manager = LoginManager()
login_manager.login_view='login'
login_manager.init_app(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def home():
    if not session.get("username"):
        return redirect("/login")
    else:
       
        rooms = get_rooms_for_user(session.get("email"))    
    return render_template("index.html", rooms=rooms)


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if session.get("username"):
    
        return redirect(url_for('home'))
    
    message = ''
    if request.method == 'POST':
        session['username']=request.form.get('username')
        session['password_input']=request.form.get('password')
        user = get_user(session['username'])
        session['email']=session['username']
     
               
        if user and user.check_password( session['password_input']): 
            session['username']=user.username
            login_user(user)
            return redirect(url_for('home'))
        else:
            message='Giriş başarısız'
    
    return render_template('login.html',message=message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if session.get("username"):
        
        return render_template('index.html')

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        save_user(username, email, password)
        return redirect(url_for('login'))
    
    return render_template('signup.html', message=message)

@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    
    if not session.get("username"):
        return redirect("/login")  
    
    message = ""
    
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip() for username in request.form.get('members').split(',')] 
      
        if len(room_name) and len(usernames): 
            room_id = save_room(room_name,  session.get("email")) 
            if session.get("email") in usernames:
                usernames.remove(session.get("email")) 
            add_room_members(room_id, room_name, usernames, session.get("email"))
            return redirect(url_for('view_room', room_id=room_id))
        else:
            message = "Oda oluşturulamadı."
    return render_template('create_room.html', message=message)

@app.route('/rooms/<room_id>/edit', methods=['GET','POST'])
def edit_room(room_id):
    if not session.get("username"):
        return redirect("/login")
    
    print("deneme deneme edit")
    room=get_room(room_id)
    if room and is_room_admin(room_id,session['email']):
        mevcut_room_member = [uye for uye in edit_room_members(int(room_id))]
        
        if request.method == 'POST':
            room_name=request.form.get('room_name')
            update_room(room_id,room_name)
            
            new_members=[username.strip() for username in request.form.get('members').split(',')]
            
            members_to_add = list(set(new_members) - set(mevcut_room_member))
            
            members_to_remove = list(set(mevcut_room_member) - set(new_members))
            print(members_to_remove," silinen elemanlar")
            
            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add,session['username'] )
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
        
        
        oda_uye_str=",".join(mevcut_room_member)
        return render_template('edit_room.html',room=room[1],room_members_str=oda_uye_str)
    else:
        return "Oda bulunamadı.",404
    
@app.route('/rooms/<room_id>/')
def view_room(room_id):
    
    if not session.get("username"):
        return redirect("/login") 
    
   
    room=get_room(room_id)
    if room and is_room_member(room_id,session['email']): 
        room_uye=get_room_members(room_id) 
        print("room üye = ",room_uye)
        message=get_message(room_id)
        return render_template('view_room.html',username =session.get("username") ,room=room,room_members=room_uye,messages=message)
    else:
        return "Oda bulunamadı",404


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{},{} numaralı odaya mesaj gönderdi: {}".format(data['username'],data['room'],data['message']))
    
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    
    str= data['room'] 
    
    save_message(str,data['message'],data['username']) 
    
    socketio.emit('receive_message', data, room=data['room']) 

@socketio.on('join_room')
def handle_join_room_event(data): 
    app.logger.info("{} adlı kullanıcı {} odasına katıldı".format(data['username'],data['room']))
    join_room(data['room']) 
    socketio.emit('join_room_announcement',data) 

@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} Adlı kullanıcı {} odasından ayrıldı".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])

@login_manager.user_loader
def load_user(username):
    return get_user(username)

if __name__ == '__main__':
    socketio.run(app,debug=True,host='0.0.0.0')

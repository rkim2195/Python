import re
from flask import Flask, render_template, redirect, request, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL

SCHEMA = 'mydb'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
INVALID_PASSWORD_REGEX = re.compile(r'^([^0-9]*|[^A-Z]*)$')

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "root"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users/create', methods=['POST'])
def register_user():
    is_valid = True
    
    if len(request.form['first_name']) < 2:
        is_valid = False
        flash("First name must be at least 2 characters long")
    print("it is less than two")
    if len(request.form['last_name']) < 2:
        is_valid = False
        flash("Last name must be at least 2 characters long")
    if len(request.form['password']) < 8:
        is_valid = False
        flash("Password must be at least 8 characters long")
    if request.form['password'] != request.form['confirm']:
        flash("Passwords must match")
        valid = False
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Please use a valid email address")

    if is_valid:
        mysql = connectToMySQL('mydb')
        query = "INSERT into users (fname, lname, password, email, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(pass)s, %(email)s, NOW(), NOW())"
        data = {
            'fn': request.form['first_name'],
            'ln': request.form['last_name'],
            'pass': bcrypt.generate_password_hash(request.form['password']),
            'email': request.form['email']
        }
        user_id = mysql.query_db(query, data)
        session['user_id'] = user_id
        return redirect('/')
    else:
        return redirect('/')

@app.route('/back')
def back():
    return redirect('/wall')

@app.route("/login", methods=["POST"])
def login_user():
    is_valid = True

    if len(request.form['email']) < 1:
        is_valid = False
        flash("Please enter your email")
    if len(request.form['password']) < 1:
        is_valid = False
        flash("Please enter your password")
    
    if not is_valid:
        return redirect("/")
    else:
        mysql = connectToMySQL('mydb')
        query = "SELECT * FROM users WHERE users.email = %(email)s"
        data = {
            'email': request.form['email']
        }
        user = mysql.query_db(query, data)
        if user:
            hashed_password = user[0]['password']
            if bcrypt.check_password_hash(hashed_password, request.form['password']):
                session['user_id'] = user[0]['idUsers']
                return redirect("/wall")
            else:
                flash("Password is invalid")
                return redirect("/")
        else:
            flash("Please use a valid email address")
            return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route("/wall")
def wall_landing():
    if 'user_id' not in session:
        return redirect("/")
    
    mysql = connectToMySQL('mydb')
    query = "SELECT * FROM users WHERE users.idusers = %(id)s"
    data = {'id': session['user_id']}
    user = mysql.query_db(query, data)

    mysql = connectToMySQL('mydb')
    query = "SELECT *, count(messages_idmessages) as likes FROM messages JOIN users ON messages.author = users.idusers LEFT JOIN users_likes_messages ON messages.idmessages = users_likes_messages.messages_idmessages GROUP BY messages.idmessages"
    messages = mysql.query_db(query)

    #mysql = mysqlconnection('mydb')
    mysql = connectToMySQL('mydb')
    query = "select * from users_likes_messages WHERE users_idusers = %(id)s"
    is_liked = mysql.query_db(query, data)
    print(is_liked)

    mysql = connectToMySQL('mydb')
    query = "select * from messages WHERE author = %(id)s"
    data = {'id': session['user_id']}
    my_msgs = mysql.query_db(query, data)
    print('poop' + str(messages))
    print('yo' + str(session['user_id']))

    liked_messages = []
    for liked in is_liked:
        liked_messages.append(liked['messages_idmessages'])    
    print(liked_messages)

    return render_template("/wall.html", user=user[0], messages=messages, liked_messages=liked_messages, my_msgs=my_msgs, my_id=session['user_id'])

@app.route("/post_message",methods=['POST'])
def commit_message():
    #mysql = mysqlconnection('mydb')
    is_valid=True

    if len(request.form['a_message_content']) < 4:
        is_valid = False
        flash("More than 3 characters")
    if len(request.form['q_message_content']) < 4:
        is_valid = False
        flash("More than 3 characters")

    if is_valid:
        mysql = connectToMySQL('mydb')
        query = "INSERT into messages(message_content, author, created_at, updated_at) VALUES (%(mess)s, %(aid)s, NOW(), NOW())"
        data = {
            "mess": request.form['a_message_content'] + ":" + request.form['q_message_content'],
            "aid": session['user_id']
            
        }
        message_id = mysql.query_db(query, data)
    
    return redirect("/wall")

@app.route("/like/<m_id>")
def like_message(m_id):
    #mysql = mysqlconnection('mydb')
    mysql = connectToMySQL('mydb')
    query = "INSERT INTO users_likes_messages (users_idusers, messages_idmessages, created_at, updated_at) VALUES (%(uid)s, %(mid)s, NOW(), NOW())"
    data = {
            'uid': session ['user_id'],
            'mid': m_id
        }
    user = mysql.query_db(query, data)
    return redirect("/wall")

@app.route("/delete/<m_id>")
def delete_message(m_id):

    query = "DELETE FROM users_likes_messages WHERE messages_idmessages = %(mid)s"
    data = {
        'mid': m_id,
        'id': session['user_id']
    }
    mysql = connectToMySQL('mydb')
    mysql.query_db(query, data)

    query = "DELETE FROM messages WHERE idmessages = %(mid)s"
    data = {
        'mid': m_id,
        'id': session['user_id']
    }
    mysql = connectToMySQL('mydb')
    mysql.query_db(query, data)
    return redirect("/wall")

@app.route("/details/<m_id>")
def message_details(m_id):
    #mysql = mysqlconnection('mydb')
    mysql = connectToMySQL('mydb')
    query = "SELECT * FROM messages LEFT JOIN users ON messages.author = users.idusers WHERE messages.idmessages = %(mid)s"
    data = {
        'mid': m_id
    }
    messages = mysql.query_db(query, data)
    mysql = connectToMySQL('mydb')
    query = "SELECT * FROM users_likes_messages LEFT JOIN users ON users_idusers = users.idusers WHERE messages_idmessages =  %(mid)s"
    data = {
        'mid': m_id
    }
    users_who_liked = mysql.query_db(query, data)
    print("0")
    print("here i am")
    return render_template("details.html", messages=messages[0], users_who_liked=users_who_liked)

@app.route("/unlike/<m_id>")
def unlike_message(m_id):
    #mysql = mysqlconnection('mydb')
    mysql = connectToMySQL('mydb')
    query = "DELETE FROM users_likes_messages WHERE users_idusers= %(uid)s AND messages_idmessages = %(mid)s"
    data = {'uid': session['user_id'],
            'mid': m_id}
    mysql.query_db(query, data)
    return redirect ("/wall")

@app.route("/edit")
def edit_user():
    query = "SELECT * FROM users WHERE idUsers = %(id)s"
    data = {
        'id': session['user_id']
    }
    mysql = connectToMySQL('mydb')
    user = mysql.query_db(query, data)
    return render_template("edit.html", user=user[0])

@app.route("/edit", methods=['POST'])
def update_user():
    query = "UPDATE users SET fname=%(fn)s, lname=%(ln)s, email=%(email)s, updated_at=NOW() WHERE idusers=%(id)s"
    data = {
        'fn': request.form['fname'],
        'ln': request.form['lname'],
        'email': request.form['email'],
        'id': session['user_id']
    }
    mysql = connectToMySQL('mydb')
    mysql.query_db(query, data)
    return redirect("/wall")

if __name__ == "__main__":
    app.run(debug=True)

from datetime import datetime
import re
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import openai
import chat_bot_api
import random
import os
import pymysql.cursors
import pymysql
import psycopg2


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s: %(message)s")
file_handler = logging.FileHandler("static/faileduser.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

app = Flask(__name__)

#used to assign session cookies/secure the cookies
secret = os.environ.get('secret_key')
app.secret_key = secret

#used to keep track of previous messagers/messages
lastMessage = ""
lastIndex = random.randint(0, 3)

#chatbot object
chatters = chat_bot_api.chatbot()

#confinguring python to connect to the database
host = os.environ.get('host')
user = os.environ.get('user')
database = os.environ.get('database')
password = os.environ.get('password')

db = psycopg2.connect(host=host,
                     user=user, password=password,database=database)
cursor = db.cursor()


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    """the login method will allow you to enter you username and password
    and if it is stored in the database
    will allow you to access the rest of the pages"""

    if "loggedin" in session:
        return render_template('chatroom.html', username=session['username'], active="true")
    
    message = "Please login"

    #if the username and password are entered it will query the database to see if they are saved
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form \
            and 'api-key' in request.form:

        username = request.form['username']
        password = request.form['password']
        language = request.form['language'] #User Selected Language Variable to be Passed to the Prompt
        key = request.form['api-key']  #API KEY Variable

        chatters.set_language(language)

        sql = "SELECT * FROM accounts WHERE username = %s and passwords = %s"
        cursor.execute(sql, (username, password,))
        account = cursor.fetchone()
        
        #using the session to confirm login and allow access to webpages.
        #Session will restrict access if not logged in
        #will also log all failed attempts to log in
        if not account:
            logger.info("%s %s failed to log in", username, request.remote_addr)
            message = 'Incorrect username/password!'

        #starting session if your account exists
        else:
            logger.info("%s %s login successful", username, request.remote_addr)
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['key'] = key
            return redirect(url_for('index2'))

    return render_template('login.html', message=message)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """this method will allow the user to register their username
and password and check to make sure that they fall within specificed
parameters"""

    if "loggedin" in session:
        return render_template('chatroom.html', username=session['username'], active="true")
    
    message = "Please register to continue"

    #will just reload the register template
    if request.method == 'GET':
        return render_template('register.html')

    #pulling the information from the page and saving it in variables
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'confirm-password' in request.form:
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm-password'] #User Password Confirmation Variable

        sql = "SELECT * FROM accounts WHERE username = %s"
        cursor.execute(sql, (username,))
        exists = cursor.fetchone()
        
        if exists:
            message = "That username is already exists!"
        #using regular expression to check username is valid
        elif not re.match(r'[A-Za-z0-9]*$', username):
            message= 'Username must contain only letters and numbers!'

        #checking any new registration against the list
        elif not check_list(password):
            message = "That is a commonly used password and is not valid!"

        #using password check function to make sure password is valid
        elif not password_check(password):
            message= ('The password must contain lowercase, uppercase, symbols,'
            'and numbers and be at least 12 characters long!')
        
        #making sure the user typed the same password for the two password inputs
        elif password != confirm:
            message = ('Your two password inputs did not match!')
            
        #if everything checks out it will save the information into the SQL database
        #will use SQL to insert the username and password into a running
        #database and redirect to login once registered
        else:
            #this cursor allows the actual interaction with the database
            sql = "INSERT INTO accounts VALUES (NULL, %s, %s)"
            cursor.execute(sql, (username, password,))
            db.commit()
            return redirect(url_for('login'))

    #if username and password left blank it will request you fill in info
    elif request.method == 'POST':
        message = 'Please enter the required information!'

    return render_template('register.html', message=message)


#renders template for main chatroom
@app.route('/chatroom', methods=['GET', 'POST'])
def index2():

    if "loggedin" in session:
        return render_template('chatroom.html', username=session['username'], active="true")
    else:
        return render_template('chatroom.html', username="Not Logged In User", active="false")


#function to get chatbot responses to the user
@app.route("/get")
def get_bot_response():

    if "loggedin" in session:
        global lastIndex
        global lastMessage

        key = session['key']
        userText = request.args.get('message')

        # add getting the index here
        index = lastIndex

        #If the user decides not to type in the start of the session
        if (userText == ""):
            userText = "Hello"
            
        # getting an index of a different artificial chatter than the last one
        if (lastMessage == userText):
            index = random.choice([number for number in [0, 1, 2, 3] if number != lastIndex])

        response = chatters.generateChatResponse(userText, key, index)
        lastMessage = response[1]
        lastIndex = index
        return response

    else:
        return ["ALERT", "Please login"]


@app.route('/logout')
def logout():
    """this method will allow for log out and return to restricted access"""

    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return redirect(url_for('login'))

def check_list(password):
    """This method will open and read the common password file and check
    any new password entered against it"""

    #opeing and reading file and closing it
    with open ("static/CommonPassword.txt", "r", encoding="utf-8") as f_read:
        reader = f_read.readlines()
        f_read.close()
        check = True

    #using a for loop to check the list
        for item in reader:
            if password == item.strip():
                check = False
    return check

def password_check(password):
    """This method will check that the password is within required specs"""

    #used for password check
    len_error = len(password) < 12
    digit_error = re.search(r"\d", password) is None
    upper_error = re.search(r"[A-Z]", password) is None
    lower_error = re.search(r"[a-z]", password) is None
    symbol_error = re.search(r"\W", password) is None
    password_ok = not(len_error or digit_error or upper_error or
                      lower_error or symbol_error)

    return password_ok

if __name__== '__main__':
    app.run()

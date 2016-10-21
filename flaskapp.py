from collections import Counter
import csv
import sqlite3
import urllib
import hmac

from flask import Flask, request, g, render_template, redirect, url_for

#DATABASE = '/var/www/html/flaskapp/adserver.db'
USERNAME = None

app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    #return sqlite3.connect(app.config['DATABASE'])
    return sqlite3.connect('adserver.db')

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

secret1 = "GeneDerSu@gofind.ai-0912u90jds"
secret2 = "lmcxvlcxm10-980ucvjn2l3mrec0jl"
def make_secure_username(val):
    return hmac.new(secret1, val).hexdigest()
def make_secure_password(val):
    return hmac.new(secret2, val).hexdigest()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        # retrive + url encoding for all fields
        username = urllib.quote_plus(request.form['username'])
        password = urllib.quote_plus(request.form['password'])
        verify = urllib.quote_plus(request.form['verify'])
        
        # check for valid entries
        if len(username) > 250:
            return render_template("signup.html",
                                   error_username='length of username > 250')
        if len(username) == 0:
            return render_template("signup.html",
                                   username=urllib.unquote_plus(username),
                                   error_username='no username entered')
        if len(password) > 250:
            return render_template("signup.html",
                                   error_password='length of password > 250')
        if len(password) == 0:
            return render_template("signup.html",
                                   error_password='no password entered')
        if password != verify:
            return render_template("signup.html",
                                   error_varify='passwords do not match')

        # hash + salt for username and password
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)

        # check for duplicated usernames
        rows = select_query("""SELECT COUNT(*) FROM user WHERE username = ?""",
                            [secured_username])
        if rows[0][0] != 0:
            return render_template("signup.html",
                                   error_username='username already exist')

        # if all correct, store the data into database and redirect to welcomeback page
        insert_query("""INSERT INTO user (username, password, bill)
                        VALUES (?,?,0)""",
                      [secured_username, secured_password])
        global USERNAME
        USERNAME = secured_username
        return redirect(url_for('welcomeback'))
    else:
        return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # retrive + url encoding for all fields
        username = urllib.quote_plus(request.form['username'])
        password = urllib.quote_plus(request.form['password'])
        
        # hash + salt for username and password
        secured_username = make_secure_username(username)
        secured_password = make_secure_password(password)
        
        # query for the user in database
        rows = select_query("""SELECT COUNT(*) FROM user WHERE username = ? AND password = ?""",
                            [secured_username, secured_password])

        # if user exist, sent to welcomeback page. else disply error
        if rows[0][0] == 1:
            global USERNAME
            USERNAME = secured_username
            return redirect(url_for('welcomeback'))
        else:
            return render_template("login.html",
                                   username=urllib.unquote_plus(username),
                                   error_username="user not exist or incorrect password")
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    global USERNAME
    USERNAME = None
    return redirect(url_for('index'))

@app.route('/welcomeback')
def welcomeback():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        # query information and pass them to html
        bill = select_query("""SELECT bill FROM user WHERE username = ?""",
                            [USERNAME])[0][0]
        #print bill
        #print select_query("""SELECT * FROM user""")
        #print select_query("""SELECT * FROM campaign""")
        items = select_query("""SELECT id, category, budget, min_bid,
                                max_bid, ad_url, description, current_cost
                                FROM campaign WHERE username = ? AND active = ?""",
                             [USERNAME, True])
        
        # TODO: add feature to deactative the campaign on the sence

        return render_template("welcomeback.html", bill=bill, items=items)

@app.route('/newcampaign', methods=['GET', 'POST'])
def newcampaign():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            pass
        else:
            return render_template("newcampaign.html")

@app.route('/modify/<int:campaign_id>', methods=['GET', 'POST'])
def modify(campaign_id):
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        # TODO: make sure the user own the campaign
        return render_template("modify.html")

@app.route('/payment')
def payment():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        return render_template("payment.html")

@app.route('/bill')
def bill():
    # check if the user is logged in
    if not USERNAME:
        return redirect(url_for('index'))
    else:
        return render_template("bill.html")

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def select_query(query, args=()):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return rows

def insert_query(query, args=()):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()
    conn.close()

if __name__ == '__main__':
  app.run()


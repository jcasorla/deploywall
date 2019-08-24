from flask import Flask, render_template, request, redirect,session, flash
from mysqlconnection import connectToMySQL
import re	# the regex module
from flask_bcrypt import Bcrypt 
import datetime       



#secret key required for session
app = Flask(__name__)
app.secret_key = 'keep it secret, keep it safe' # set a secret key for security purposes
bcrypt = Bcrypt(app)     # we are creating an object called bcrypt, 
                         # which is made by invoking the function Bcrypt with our app as an argument

myDB='flask_practice'

# create a regular expression object that we'll use later   
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/users', methods=['POST'])
def create_user():
    print("Got Post Info")
    print(request.form)
    
    failed=False
    
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==True):            
            flash("Please chose another email")
            failed=True

    if len(request.form['first_name']) < 1:
        flash("first name cannot be blank!")
        failed=True
    if len(request.form['last_name']) < 1:
        flash("last name cannot be blank!")
        failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True
    if len(request.form['cpwd']) < 1:
        flash("confirm password cannot be blank!")
        failed=True
    if request.form['pwd'] != request.form['cpwd']:
        flash("Passwords do not match")
        failed=True
        

    if(failed==True):
        return redirect("/")

    
    elif not '_flashes' in session.keys():	# no flash messages means all validations passed
        pw_hash = bcrypt.generate_password_hash(request.form['pwd'])
                
        query="insert into users (first_name,last_name,email,password,created_at,updated_at)  values (%(fn)s,%(ln)s,%(em)s,%(pw)s, NOW(),NOW());"

        data = {
            "fn": request.form['first_name'],
            "ln": request.form['last_name'],
            "em": request.form['email'],
            "pw": pw_hash
        }
        mysql = connectToMySQL(myDB)
        id=mysql.query_db(query,data)
        print(id)

        query2="select * from users where id=%(id)s"
        data2 = {
            "id": id            
        }

        mysql = connectToMySQL(myDB)
        user=mysql.query_db(query2,data2)[0]

        session['id']=id
        session['name']=user['first_name']
        return redirect('/books')


@app.route('/login', methods=['POST'])
def login():
    failed=False
    if len(request.form['email']) < 1:
        flash("Email cannot be blank!")
        failed=True
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
        failed=True
    else:
        query2="select * from users where email=%(em)s"
        data2 = {
        "em": request.form['email']            
        }
        mysql = connectToMySQL(myDB)
        emailv=mysql.query_db(query2,data2)
        if(bool(emailv)==False):            
            flash("Unable to Login")
            failed=True

    if len(request.form['pwd']) < 1:
        flash("password cannot be blank!")
        failed=True

    elif not '_flashes' in session.keys():
        print(request.form["email"])
        mysql = connectToMySQL(myDB)
        query = "SELECT * FROM users WHERE email like %(em)s;"
        data = { "em" : request.form["email"] }
        result = mysql.query_db(query, data)
        if len(result) > 0:
            if bcrypt.check_password_hash(result[0]['password'], request.form['pwd']):
                # if we get True after checking the password, we may put the user id in session
                #change it to session['id']
                session['id'] = result[0]['id']
                session['name'] = result[0]['first_name']
                # never render on a post, always redirect!
                # return redirect('/success')
            else:
                flash("Unable to Login")
                print("Unable to login")
                failed=True

    if(failed==True):
        return redirect("/")
    else:
        return redirect("/books")

@app.route('/books')
def showbooks():
    #select * from books b join favorites f on b.id=f.book_id join users u on f.user_id=u.id where u.id=2=%(u_id)s;
    #select * from books b join favorites f on b.id=f.book_id join users u on f.user_id=u.id where u.id=4\G
    #select b.id,b.title,u.first_name,u.last_name,u.id as user_id from books b join users u on b.uploaded_by_id=u.id
    #select b.id, distinct(b.title),u.first_name,u.last_name,u.id as user_id, f.user_id from books b join users u on b.uploaded_by_id=u.id join favorites f on u.id=f.user_id;
    #select distinct b.id,b.title,u.first_name,u.last_name,u.id as user_id, f.user_id as fav_id from books b join users u on b.uploaded_by_id=u.id join favorites f on f.book_id=b.id;

    #select distinct b.id,b.title,u.first_name,u.last_name,u.id as user_id from books b join users u on b.uploaded_by_id=u.id order by b.id;

    #previous:
    #select b.id,b.title,u.first_name,u.last_name,u.id as user_id from books b join users u on b.uploaded_by_id=u.id;

    #select b.id,b.title,u.first_name,u.last_name,u.id as user_id, (select distinct user_id from favorites where user_id=u.id) as fav_id from books b join users u on b.uploaded_by_id=u.id where u.id in(select user_id from favorites where user_id=u.id);
    
    #******************************************************************************************
    #best way and then split contents of fav_id into a list from their you can manipulate it:
    #select b.id,b.title,u.first_name,u.last_name,u.id as user_id, (select GROUP_CONCAT(user_id) from favorites where user_id=u.id) as fav_id from books b join users u on b.uploaded_by_id=u.id;
    #******************************************************************************************

    if(bool(session)):
        query="select b.id,b.title,u.first_name,u.last_name,u.id as user_id from books b join users u on b.uploaded_by_id=u.id;"

        data = {
            "id": session['id']
        }
        mysql = connectToMySQL(myDB)
        books=mysql.query_db(query,data)

        return render_template("show.html", all_books=books)
    else:
        return redirect("/")

@app.route('/books/new', methods=['POST'])#cant add books more than once and other validations
def insertBook():
    #validations for adding books 
    if len(request.form['title']) < 1:
        flash("Title field is required")

    else:
        query="select * from books where title=%(title)s"

        data = {
            "title": request.form['title']
        }
        mysql = connectToMySQL(myDB)
        result=mysql.query_db(query,data)

        print(type(result))

    
        if(not result):
            pass
        else:
            flash("Title exists please chose another")

    if len(request.form['description']) < 5:
        flash("Description field cannot be less than 5 characters")
    

    elif not '_flashes' in session.keys():
        query="insert into books (title,description,uploaded_by_id,created_at,updated_at)  values (%(title)s,%(desc)s,%(u_id)s, NOW(),NOW());"

        data = {
            "title": request.form['title'],
            "desc": request.form['description'],
            "u_id": session['id']
        }
        mysql = connectToMySQL(myDB)
        id=mysql.query_db(query,data)

        
        query2="insert into favorites (book_id,user_id)  values (%(book_id)s,%(user_id)s);"
        data2 = {
            "book_id": id,
            "user_id": session['id']
        }
        mysql = connectToMySQL(myDB)
        mysql.query_db(query2,data2)

    return redirect("/books")

@app.route('/books/<int:id>')
def showBook(id):
    #select b.id,b.title,b,description,b.created_at,b.updated_on,u.first_name,u.last_name from books b join users u on b.uploaded_by_id=u.id;
    #select id,title,description,created_at,updated_at from books where id=%(id)s;
    query="select b.id,b.title,b.description,b.created_at,b.updated_at,u.id as user_id,u.first_name,u.last_name from books b join users u on b.uploaded_by_id=u.id where b.id=%(id)s"

    data = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    book=mysql.query_db(query,data)[0]
    # x=datetime.datetime(book['created_at'])
    # print(x.strptime("%b %d %Y %H:%M"))
    # x=book['created_at']
    # x.strptime
    

    query2="select u2.id as user_id,u2.first_name, u2.last_name from books b join favorites f on b.id=f.book_id join users u2 on f.user_id=u2.id where b.id=%(id)s"

    data2 = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    fav_users=mysql.query_db(query2,data2)

    return render_template("show_book.html", book=book, fav_users=fav_users)

@app.route('/books/<int:id>/update', methods=['POST'])
def update(id):


    if len(request.form['title']) < 1:
        flash("Title field is required")
    if len(request.form['description']) < 5:
        flash("Description field cannot be less than 5 characters")
    
    elif not '_flashes' in session.keys():

        query="update books set title=%(title)s,description=%(desc)s where id=%(id)s"

        data = {
            "id": id,
            "title": request.form['title'],
            "desc": request.form['description']
        }
        mysql = connectToMySQL(myDB)
        mysql.query_db(query,data)
    
    return redirect(f"/books/{id}")

@app.route('/books/<int:id>/delete')
def delete(id):
    query="delete from favorites where book_id=%(book_id)s;"
    data = {
        "book_id": id,
        "user_id": session['id']
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)
    
    query="delete from books where id=%(id)s"

    data = {
        "id": id
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)
    
    return redirect("/books")

@app.route('/books/<int:id>/fav')
def fav(id):
    query="insert into favorites (book_id,user_id)  values (%(book_id)s,%(user_id)s);"
    data = {
        "book_id": id,
        "user_id": session['id']
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)

    return redirect(f"/books/{id}")

@app.route('/books/<int:id>/unfav')
def unfav(id):
    query="delete from favorites where book_id=%(book_id)s and user_id=%(user_id)s;"
    data = {
        "book_id": id,
        "user_id": session['id']
    }
    mysql = connectToMySQL(myDB)
    mysql.query_db(query,data)

    return redirect(f"/books/{id}")

@app.route('/logout')
def logout():

    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)  
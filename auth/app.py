from flask import Flask, render_template, redirect, url_for, session, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'asops_db_book'
app.secret_key = 'key'

mysql = MySQL(app)

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        # store data into database 
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where id=%s",(user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            return render_template('dashboard.html',user=user)
            
    return redirect(url_for('login'))


@app.route('/dashboard/book_list')
def book_list():

    cursor = mysql.connection.cursor()
    cursor.execute("Select * from books")
    data = cursor.fetchall()
    cursor.close()
    return render_template('book_list.html', books=data)

@app.route('/dashboard/book_form')
def book_form():
    return render_template('book_form.html')

@app.route('/dashboard/book_form/insert', methods=['POST'])
def insert():
    if request.method == "POST":
        try:
            title = request.form['title']
            author = request.form['author']
            gerne = request.form['gerne']
            detail = request.form['detail']

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO books (title, author, gerne, detail) VALUES (%s, %s, %s, %s)", 
                               (title, author, gerne, detail))
            mysql.connection.commit()
            cursor.close()

            flash("Book added successfully")
            return redirect(url_for('book_list'))
        except Exception as e:
            flash(f"An error occurred: {e}")
            return redirect(url_for('book_form'))
        

@app.route('/dashboard/book/<int:book_id>')
def view_book(book_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
    book = cursor.fetchone()
    cursor.close()
    return render_template('view_book.html', book=book)

@app.route('/dashboard/book/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM books WHERE id=%s", (book_id,))
        book = cursor.fetchone()
        cursor.close()
        return render_template('edit_book.html', book=book)

    if request.method == 'POST':
        try:
            title = request.form['title']
            author = request.form['author']
            gerne = request.form['gerne']
            detail = request.form['detail']

            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE books SET title=%s, author=%s, gerne=%s, detail=%s WHERE id=%s", 
                               (title, author, gerne, detail, book_id))
                
            mysql.connection.commit()
            cursor.close()

            flash("Book updated successfully")
            return redirect(url_for('book_list'))

        except Exception as e:
            flash(f"An error occurred: {e}")
            return redirect(url_for('edit_book', book_id=book_id))

@app.route('/dashboard/book/delete/<int:book_id>')
def delete_book(book_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM books WHERE id=%s", (book_id,))
        mysql.connection.commit()
        cursor.close()

        flash("Book deleted successfully")
    except Exception as e:
        flash(f"An error occurred: {e}")

    return redirect(url_for('book_list'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
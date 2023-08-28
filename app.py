from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import mysql.connector

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER


app.secret_key = 'your_secret_key'
logged_in_fullname = ""
# MySQL Connection
db = mysql.connector.connect(
    host='localhost',
    user="root",
    password="root",
    database="students"
)
cursor = db.cursor()

def create_users_table():
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        fullname VARCHAR(255),
        rollnumber VARCHAR(255),
        branch VARCHAR(255),
        phonenumber VARCHAR(255),
        email VARCHAR(255),
        idcardphoto VARCHAR(255),
        password VARCHAR(255)
    )
    """
    cursor.execute(query)
    db.commit()

def create_items_table():
    query = """
    CREATE TABLE IF NOT EXISTS items_for_sale (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_name VARCHAR(255),
        item_price DECIMAL(10, 2),
        seller_name VARCHAR(255)
    )
    """
    cursor.execute(query)
    db.commit()






@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in_fullname
    if request.method == 'POST':
        rollnumber = request.form['rollnumber']
        password = request.form['password']

        query = "SELECT * FROM users WHERE rollnumber = %s AND password = %s"
        cursor.execute(query, (rollnumber, password))
        user = cursor.fetchone()

        if user:
            logged_in_fullname = user[1]
            session['user_id'] = user[0]  # Store user ID in session
            flash("Login successful!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid roll number or password.", 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        rollnumber = request.form['rollnumber']
        branch = request.form['branch']
        phonenumber = request.form['phonenumber']
        email = request.form['email']
        idcardphoto = request.files['idcardphoto']  # Get the uploaded file
        password = request.form['password']

        if idcardphoto:
                # Generate a unique filename using a timestamp
                current_time = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{current_time}_{secure_filename(idcardphoto.filename)}"
                
                image_path = os.path.join(app.root_path, 'static', 'uploads', filename).replace("\\", "/")
                idcardphoto.save(image_path)

                # Store the image path in the database
                query = """
                INSERT INTO users (fullname, rollnumber, branch, phonenumber, email, idcardphoto, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (fullname, rollnumber, branch, phonenumber, email, image_path, password))
                db.commit()

                flash("Registration successful! You can now log in.", 'success')
                return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/user_profile')
def user_profile():
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Fetch the user's details from the database
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user_details = cursor.fetchone()

        if user_details:
            return render_template('user_profile.html', user=user_details)
        else:
            flash("User details not found.", 'error')
            return redirect(url_for('dashboard'))
    else:
        flash("Please log in to view your profile.", 'error')
        return redirect(url_for('login'))
    


@app.route('/seller_profile/<string:seller_name>')
def seller_profile(seller_name):
    # Fetch seller's details from the database based on seller_name
    query = "SELECT * FROM users WHERE fullname = %s"
    cursor.execute(query, (seller_name,))
    seller_details = cursor.fetchone()

    if seller_details:
        return render_template('seller_profile.html', seller=seller_details)
    else:
        flash("Seller details not found.", 'error')
        return redirect(url_for('buy_sell'))
    


@app.route('/buy_sell')
def buy_sell():
    # Fetch items for sale from the database
    query = "SELECT * FROM items_for_sale"
    cursor.execute(query)
    items = cursor.fetchall()

    # Create a list of items with additional seller information
    updated_items = []
    for item in items:
        seller_name = item[3]  # Assuming seller_name is in the fourth column
        updated_items.append((*item, seller_name))

    # Pass the updated items to the template
    return render_template('buy_sell.html', items=updated_items)


@app.route('/sell_item', methods=['GET', 'POST'])
def sell_item():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_price = request.form['item_price']
        
        # Insert item details into the database
        query = "INSERT INTO items_for_sale (item_name, item_price, seller_name) VALUES (%s, %s, %s)"
        cursor.execute(query, (item_name, item_price, logged_in_fullname))
        db.commit()

        flash("Item added to market!", 'success')
        return redirect(url_for('buy_sell'))

    return render_template('sell_item.html')


@app.route('/view_product/<int:item_id>')
def view_product(item_id):
    # Fetch item details from the database based on item_id
    query = "SELECT * FROM items_for_sale WHERE id = %s"
    cursor.execute(query, (item_id,))
    item = cursor.fetchone()

    return render_template('view_product.html', item=item)





@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    create_users_table()
    create_items_table()  
    app.run(debug=True)
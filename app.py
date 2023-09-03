from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import mysql.connector
from datetime import datetime


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
def create_rent_table():
    query = """
    CREATE TABLE IF NOT EXISTS rental_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        item_name VARCHAR(255),
        item_price DECIMAL(10, 2),
        seller_name VARCHAR(255)
    )
    """
    cursor.execute(query)
    db.commit()
def job_postings():
    query = """
    CREATE TABLE IF NOT EXISTS job_postings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        role_name VARCHAR(255) NOT NULL,
        skills TEXT,
        description TEXT NOT NULL,
        duration VARCHAR(255) NOT NULL,
        seller_name VARCHAR(255)
    )
    """
    cursor.execute(query)
    db.commit()

def create_rides_table():
    query = """
    CREATE TABLE IF NOT EXISTS rides (
        id INT AUTO_INCREMENT PRIMARY KEY,
        start_location VARCHAR(255) NOT NULL,
        start_time VARCHAR(50) NOT NULL,
        price FLOAT NOT NULL,
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


@app.route('/hire_person_details/<string:seller_name>')
def hire_person_details(seller_name):
    # Fetch seller's details from the database based on seller_name
    query = "SELECT * FROM users WHERE fullname = %s"
    cursor.execute(query, (seller_name,))
    seller_details = cursor.fetchone()

    if seller_details:
        return render_template('hire_person_details.html', seller=seller_details)
    else:
        flash("Seller details not found.", 'error')
        return redirect(url_for('jobs'))




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

@app.route('/view_my_item/<int:item_id>')

@app.route('/my_items')
def my_items():
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Fetch items posted by the user from the items_for_sale table
        query = "SELECT * FROM items_for_sale WHERE seller_name = %s"
        cursor.execute(query, (logged_in_fullname,))
        user_items = cursor.fetchall()

        return render_template('my_items.html', user_items=user_items)
    else:
        flash("Please log in to view your posted items.", 'error')
        return redirect(url_for('login'))

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Check if the item with the specified ID belongs to the logged-in user
        query = "SELECT seller_name FROM items_for_sale WHERE id = %s"
        cursor.execute(query, (item_id,))
        seller_name = cursor.fetchone()[0]

        if seller_name == logged_in_fullname:
            # Delete the item if it belongs to the logged-in user
            query = "DELETE FROM items_for_sale WHERE id = %s"
            cursor.execute(query, (item_id,))
            db.commit()
            flash("Item deleted successfully!", 'success')
        else:
            flash("You can only delete your own items.", 'error')
    else:
        flash("Please log in to delete items.", 'error')

    return redirect(url_for('my_items'))



@app.route('/buy_rent')
def buy_rent():
    # Fetch items for sale from the database
    query = "SELECT * FROM rental_items"
    cursor.execute(query)
    items = cursor.fetchall()

    # Create a list of items with additional seller information
    updated_items = []
    for item in items:
        seller_name = item[3]  # Assuming seller_name is in the fourth column
        updated_items.append((*item, seller_name))

    # Pass the updated items to the template
    return render_template('buy_rent.html', items=updated_items)


@app.route('/give_rent_item', methods=['GET', 'POST'])
def give_rent_item():
    if request.method == 'POST':
        item_name = request.form['item_name']
        item_price = request.form['item_price']
        
        # Insert item details into the database
        query = "INSERT INTO rental_items (item_name, item_price, seller_name) VALUES (%s, %s, %s)"
        cursor.execute(query, (item_name, item_price, logged_in_fullname))
        db.commit()

        flash("Item added to market!", 'success')
        return redirect(url_for('buy_rent'))

    return render_template('give_rent_item.html')
@app.route('/my_rental_items')
def my_rental_items():
    # Fetch rental items posted by the user from the rental_items table
    query = "SELECT * FROM rental_items WHERE seller_name = %s"
    cursor.execute(query, (logged_in_fullname,))
    user_rental_items = cursor.fetchall()

    return render_template('my_rental_items.html', user_rental_items=user_rental_items)
@app.route('/delete_rental_item/<int:item_id>', methods=['POST'])
def delete_rental_item(item_id):
    # Delete the rental item from the database based on the item_id
    query = "DELETE FROM rental_items WHERE id = %s AND seller_name = %s"
    cursor.execute(query, (item_id, logged_in_fullname))
    db.commit()

    flash("Rental item deleted successfully!", 'success')
    return redirect(url_for('my_rental_items'))

# Route for posting a job
@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        role_name = request.form['role_name']
        skills = request.form['skills']
        description = request.form['description']
        duration = request.form['duration']
        
        # Save the job details to the job_postings table in your database
        query = "INSERT INTO job_postings (role_name, skills, description, duration, seller_name) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (role_name, skills, description, duration, logged_in_fullname))
        db.commit()

        flash("Job listing posted successfully!", 'success')
        return redirect(url_for('jobs'))

    return render_template('post_job.html')

# Route for displaying all job postings
@app.route('/jobs')
def jobs():
    # Fetch all job postings from the job_postings table
    query = "SELECT * FROM job_postings"
    cursor.execute(query)
    job_postings = cursor.fetchall()
   # print(job_postings)

    return render_template('jobs.html', job_postings=job_postings)
@app.route('/job_details/<int:job_id>')
def job_details(job_id):
    # Fetch job details from the database using the job_id
    query = "SELECT * FROM job_postings WHERE id = %s"
    cursor.execute(query, (job_id,))
    job_details = cursor.fetchone()

    return render_template('job_details.html', job_details=job_details)
@app.route('/my_jobs')
def my_jobs():
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Fetch jobs posted by the user from the job_postings table
        query = "SELECT * FROM job_postings WHERE seller_name = %s"
        cursor.execute(query, (logged_in_fullname,))
        user_jobs = cursor.fetchall()

        return render_template('my_jobs.html', user_jobs=user_jobs)
    else:
        flash("Please log in to view your posted jobs.", 'error')
        return redirect(url_for('login'))

@app.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Delete the job with the specified ID if it belongs to the user
        query = "DELETE FROM job_postings WHERE id = %s AND seller_name = %s"
        cursor.execute(query, (job_id, logged_in_fullname))
        db.commit()
        flash("Job deleted successfully!", 'success')
    else:
        flash("Please log in to delete jobs.", 'error')

    return redirect(url_for('my_jobs'))


@app.route('/view_rides')
def view_rides():
    # Fetch ride details from the rides table
    query = "SELECT * FROM rides"
    cursor.execute(query)
    rides = cursor.fetchall()
    
    return render_template('view_rides.html', rides=rides)
@app.route('/share_vehicle', methods=['GET', 'POST'])
def share_vehicle():
    if request.method == 'POST':
        start_location = request.form['start_location']
        start_time = request.form['start_time']
        price = request.form['price']

        # Insert the ride details into the rides table
        query = "INSERT INTO rides (start_location, start_time, price, seller_name) VALUES (%s, %s, %s,%s)"
        cursor.execute(query, (start_location, start_time, price, logged_in_fullname))
        db.commit()

        flash("Vehicle availability posted successfully!", 'success')
        return redirect(url_for('share_vehicle'))

    # Fetch ride details from the rides table
    query = "SELECT * FROM rides"
    cursor.execute(query)
    rides = cursor.fetchall()

    return render_template('share_vehicle.html', rides=rides)
@app.route('/sharer_profile/<string:seller_name>')
def sharer_profile(seller_name):
    # Fetch seller's details from the database based on seller_name
    query = "SELECT * FROM users WHERE fullname= %s"
    cursor.execute(query, (seller_name,))
    seller_details = cursor.fetchone()

    if seller_details:
        return render_template('sharer_profile.html', seller=seller_details)
    else:
        flash("Seller details not found.", 'error')
        return redirect(url_for('buy_sell'))

@app.route('/my_rides')
def my_rides():
    user_id =session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Fetch rides posted by the user from the rides table
        query = "SELECT * FROM rides WHERE seller_name = %s"
        cursor.execute(query, (logged_in_fullname,))
        user_rides = cursor.fetchall()

        return render_template('my_rides.html', user_rides=user_rides)
    else:
        flash("Please log in to view your posted rides.", 'error')
        return redirect(url_for('login'))


@app.route('/delete_ride/<int:ride_id>', methods=['POST'])
def delete_ride(ride_id):
    user_id = session.get('user_id')  # Get the user's ID from the session
    if user_id:
        # Delete the job with the specified ID if it belongs to the user
        query = "DELETE FROM rides WHERE id = %s AND seller_name = %s"
        cursor.execute(query, (ride_id, logged_in_fullname))
        db.commit()
        flash("Ride deleted successfully!", 'success')
    else:
        flash("Please log in to delete Rides.", 'error')

    return redirect(url_for('my_rides'))















@app.route('/view_product/<int:item_id>')
def view_product(item_id):
    # Fetch item details from the database based on item_id
    query = "SELECT * FROM items_for_sale WHERE id = %s"
    cursor.execute(query, (item_id,))
    item = cursor.fetchone()

    return render_template('view_product.html', item=item)

@app.route('/view_product_2/<int:item_id>')
def view_product_2(item_id):
    # Fetch item details from the database based on item_id
    query = "SELECT * FROM rental_items WHERE id = %s"
    cursor.execute(query, (item_id,))
    item = cursor.fetchone()

    return render_template('view_product_2.html', item=item)




@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    create_users_table()
    create_items_table() 
    create_rent_table() 
    job_postings()
    create_rides_table()
    app.run(debug=True)
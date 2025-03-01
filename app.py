import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash
from tensorflow import keras
from keras.models import load_model
from keras.preprocessing import image
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
import hashlib
from flask import Flask, render_template, request, redirect, url_for



# Load environment variables from .env file
load_dotenv()


print("SECRET_KEY:", os.getenv("SECRET_KEY"))
print("MYSQL_HOST:", os.getenv("MYSQL_HOST"))
print("MYSQL_USER:", os.getenv("MYSQL_USER"))
print("MYSQL_PASSWORD:", os.getenv("MYSQL_PASSWORD"))
print("MYSQL_DB:", os.getenv("MYSQL_DB"))



app = Flask(__name__)

# Use environment variables for MySQL configuration and secret key
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)



# Disease Dictionary
dic = {0: 'cellulitis', 1: 'impetigo', 2: 'Athletes Foot', 3: 'Nail Fungus', 4: 'ringworm',
       5: 'Cutaneous Larva Migrans', 6: 'chickenpox', 7: 'shingles'}

# Load Model
model = load_model('skin.h5', compile=False)

# Image Upload Folder
UPLOAD_FOLDER = "static/upload/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

img_size = (234, 234)

# Preprocess Image
def preprocess_image(image_path):
    img = image.load_img(image_path, target_size=img_size)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Predict Image
def predict_image(img_path):
    processed_image = preprocess_image(img_path)
    preds = model.predict(processed_image)
    predicted_class_idx = np.argmax(preds)
    confidence = round(np.max(preds) * 100, 2)  # Rounded confidence score
    return predicted_class_idx, confidence

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def loginpage():
    return render_template('login.html')

@app.route('/login2', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            flash('Login successful!', 'success')
            return redirect(url_for('index2'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
        else:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('loginpage'))

    return render_template('login.html')

@app.route('/Banner')
def index2():
    return render_template('Banner.html')

@app.route('/index')
def index3():
    return render_template('index2.html')

@app.route('/submit', methods=['POST', 'GET'])
def get_output():
    if request.method == 'POST':
        img = request.files['my_image']
        if img.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        img_path = os.path.join(app.config["UPLOAD_FOLDER"], img.filename)
        img.save(img_path)
        p, accuracy = predict_image(img_path)
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM diseases WHERE srno = %s", (str(p + 1),))
        users = cur.fetchall()
        cur.close()
        
        return render_template("result.html", prediction=users[0][1], img_path=img_path, accuracy=accuracy, info=users)
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

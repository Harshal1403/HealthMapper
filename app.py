from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  # Import current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database for user data
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change to a random secret key in production

# Initialize database and login manager
db = SQLAlchemy(app) 
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to login page if not logged in

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms-of-service.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()  # Create database tables only once at the start

# Load the trained model
model = pickle.load(open('models/diabetes.pkl', 'rb'))  # Ensure the model path is correct

@app.route('/')
def home():
    return render_template('loginorsignup.html')  # Landing page for login/signup

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')  # Provide feedback
            return redirect(url_for('index'))  # Redirect to index after login
        else:
            flash('Invalid username or password', 'danger')  # Flash message for incorrect login
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash('You are already logged in. Please log out to create a new account.', 'info')
        return redirect(url_for('index'))  # Redirect to index if already logged in

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('signup'))  # Redirect back to signup if username taken

        # If username is unique, proceed with account creation
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))  # Redirect to login after successful signup
    return render_template('signup.html')


@app.route('/index')
@login_required  # Ensure the user is logged in to access this route
def index():
    return render_template('index.html')  # Show the index page with links to disease pages

@app.route('/disease1', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in to access this route
def disease1():
    prediction = None
    if request.method == 'POST':
        try:
            # Collect input data from form
            age = request.form.get('age')
            urea = request.form.get('urea')
            hba1c = request.form.get('hba1c')
            chol = request.form.get('chol')
            tg = request.form.get('tg')
            vldl = request.form.get('vldl')
            bmi = request.form.get('bmi')

            # Convert input data to floats and prepare for prediction
            input_data = np.array([[float(age), float(urea), float(hba1c),
                                    float(chol), float(tg), float(vldl), float(bmi)]])
            
            # Make prediction using the model
            prediction = model.predict(input_data)[0]
        except ValueError:
            flash("Please enter valid numerical values for all fields.", 'danger')
            return redirect(url_for('disease1'))

    # Render the disease1 page with the prediction (if available)
    return render_template('disease1.html', prediction=prediction)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')  # Optional: Provide feedback
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
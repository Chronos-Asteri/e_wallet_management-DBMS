from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
engine  = SQLAlchemy(app).engine

app.secret_key = b'_324342938749$%&&^$%4'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))    
    
class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True) #wallet_id
    user_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(200), nullable=False) # Name Of The Wallet
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Active")
    balance = db.Column(db.Integer, primary_key=False, default=0)
    bank_id = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Wallet %r>' % self.id
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Banks(db.Model):
    bank_id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), nullable=False, unique=True)
    # This could have other details of the registered banks

class Logs(db.Model):
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(20), nullable=False)
    access_time = db.Column(db.DateTime, default=datetime.now()) # This is the time recorded on this machine i.e server
    log_type = db.Column(db.String(200), nullable=False) # Login/Logged Out/Transaction/Bank Transfer
    transaction_id = db.Column(db.Integer, nullable=True)
    bank_trans_id = db.Column(db.Integer, nullable=True)   

class Transactions(db.Model): # Send/Pay
    transaction_id = db.Column(db.Integer, primary_key=True)
    trans_amt = db.Column(db.Integer, nullable=False)
    pay_cus_id = db.Column(db.Integer, nullable=False) # Transferred to whom
    user_id = db.Column(db.Integer, nullable=False) # The Person transferring 
    wallet_id = db.Column(db.Integer, nullable=False)
    trsn_time = db.Column(db.DateTime, default=datetime.now()) # This is the exact time the amount was transferred from the wallet

class BankTransfers(db.Model):
    bank_trans_id = db.Column(db.Integer, primary_key=True)
    bank_id = db.Column(db.Integer, nullable=False) # Since the wallet could update the bank, thus transaction bank and current bank will not match in some cases
    transaction_type = db.Column(db.String(200), nullable=False) ## Withdrawal (Wallet->Bank) /Loading (Bank->Wallet) Money
    bank_trans_amt = db.Column(db.Integer, nullable=False) # This is the exact time the amount was transferred from the Bank
    wallet_id = db.Column(db.Integer, nullable=False)
    bank_trsn_time = db.Column(db.DateTime, default=datetime.now())
    
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')
            
class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')
   
## Login // Logout // Register
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                new_log = Logs(user_id=user.id, username=user.username, access_time= datetime.now(), log_type="Login")
                db.session.add(new_log)
                db.session.commit()
                login_user(user)
                return redirect('/')

    return render_template('login_page.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    new_log = Logs(user_id=current_user.id, username=current_user.username, access_time= datetime.now(), log_type="Logged Out")
    db.session.add(new_log)
    db.session.commit()
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register_page.html', form=form)


## Management Functions
@app.route('/admin', methods=['POST', 'GET'])
@login_required
def admin():
    id = current_user.id
    
    if id == 1:
        tasks = User.query.order_by(User.id).all()
        return render_template('admin.html', tasks=tasks)
    else:
        flash("Only the admin as access to 'Admin' page")
        tasks = Wallet.query.filter_by(user_id=current_user.id).order_by(Wallet.date_created).all()
        return redirect(url_for('index'))



@app.route('/user_details/<int:id>', methods=['POST', 'GET'])
@login_required
def user_details(id):
    
    if current_user.id == 1:
        tasks = Wallet.query.filter_by(user_id=id).order_by(Wallet.date_created).all()
        return render_template('user_details.html', tasks=tasks) 
    else:
        flash("Only the admin as access to 'Admin' page")
        return redirect(url_for('index'))
    
      

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Wallet(user_id=current_user.id, content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'

    else:
        tasks = Wallet.query.filter_by(user_id=current_user.id).order_by(Wallet.date_created).all()
        return render_template('index.html', tasks=tasks)


@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    task_to_delete = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    try:
        flash(task_to_delete.content +" Deleted Successfully")
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    task = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your wallet name'

    else:
        return render_template('update.html', task=task)
 
@app.route('/update_bank_id/<int:id>', methods=['GET', 'POST'])   
@login_required
def update_bank_name(id):
    task = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    if request.method == 'POST':
        task.bank_id = request.form['bank_id']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your Bank Name'

    else:
        return render_template('update.html', task=task)
 
@app.route('/load_money/<int:id>', methods=['GET', 'POST'])
@login_required   
def load_money(id):
    task = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    if request.method == 'POST' and task.status == "Active":
        task.balance = str(int(task.balance) + abs(int(request.form['balance'])))

        transfer = BankTransfers(bank_id=task.bank_id, transaction_type="Loading", bank_trans_amt=int(request.form['balance']), wallet_id=id, bank_trsn_time=datetime.now())
        db.session.add(transfer)

        try:
            db.session.commit()
            new_log = Logs(user_id=current_user.id, username=current_user.username, access_time= datetime.now(), log_type="Bank Transfer", bank_trans_id=transfer.bank_trans_id)
            db.session.add(new_log)
            db.session.commit()

            flash("$ "+ str(abs(int(request.form['balance']))) +" Loaded to "+ task.content + " Successfully")
            return redirect('/')
        except:
            return 'There was an issue while loading wallet'

    else:
        flash('Cannot Complete Transaction When The Card Is Blocked')
        return render_template('update.html', task=task)
    
@app.route('/withdraw_money/<int:id>', methods=['GET', 'POST']) 
@login_required 
def withdraw_money(id):
    task = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    if request.method == 'POST' and task.status == "Active":
        
        after_wd = int(task.balance) - int(request.form['balance'])
        
        if after_wd < 0 :
            flash('Insufficients Funds')
            return render_template('update.html', task=task)
            
        else:            
            task.balance = str(int(task.balance) - abs(int(request.form['balance'])))

            transfer = BankTransfers(bank_id=task.bank_id, transaction_type="Withdrawal", bank_trans_amt=int(request.form['balance']), wallet_id=id, bank_trsn_time=datetime.now())
            db.session.add(transfer)

        try:
            db.session.commit()

            new_log = Logs(user_id=current_user.id, username=current_user.username, access_time= datetime.now(), log_type="Bank Transfer", bank_trans_id=transfer.bank_trans_id)
            db.session.add(new_log)
            db.session.commit()

            flash("$ "+ str(abs(int(request.form['balance']))) +" Withdrawn from "+ task.content + " Successfully")
            return redirect('/')
        except:
            return 'There was an issue while withdrawing from the wallet'

    else:
        flash('Cannot Complete Transaction When The Card Is Blocked')
        return render_template('update.html', task=task)
    
###############################################################
###############################################################
###############################################################


@app.route('/send_money/<int:id>', methods=['GET', 'POST']) 
@login_required 
def send_money(id):
    task = Wallet.query.filter_by(id=id).first()

    if request.method == 'POST' and task.status == "Active":
        if len(User.query.filter_by(username=request.form['recv_username']).all()) == 0: # Checking If The Username exists or not
            flash("Username Doesn't Exists")
            return render_template('transfer_amt.html', task=task)
    
        else:
            recv_id = User.query.filter_by(username=request.form['recv_username']).first().id
            reciever = Wallet.query.filter_by(user_id=recv_id).first()
        
            after_tr = int(task.balance) - int(request.form['transfer'])
            
            if after_tr < 0 :
                flash('Insufficients Funds')
                return render_template('transfer_amt.html', task=task)
            
            elif len(Wallet.query.filter_by(user_id=recv_id).all()) == 0:
                flash('Receiver does not have any wallets to recieve')
                return render_template('transfer_amt.html', task=task)
            
            else:
                reciever.balance = str(int(reciever.balance) + int(request.form['transfer']))
                task.balance = str(after_tr)

                transn = Transactions(trans_amt=int(request.form['transfer']), pay_cus_id=recv_id, user_id=current_user.id, wallet_id=id, trsn_time=datetime.now())
                db.session.add(transn)

            try:
                db.session.commit()

                new_log = Logs(user_id=current_user.id, username=current_user.username, access_time= datetime.now(), log_type="Transaction", transaction_id=transn.transaction_id)
                db.session.add(new_log)
                db.session.commit()

                flash("$ "+ str(abs(int(request.form['transfer']))) +" Was Sent To "+ User.query.filter_by(id=recv_id).first().username + " Successfully")
                return redirect('/')
            except:
                return 'There was an issue while transferring from the wallet'
        
    else:
        return render_template('transfer_amt.html', task=task)
    
###############################################################
###############################################################
###############################################################

@app.route('/status_update/<int:id>', methods=['GET', 'POST']) 
@login_required  
def status_update(id):
    task = Wallet.query.filter_by(user_id=current_user.id, id=id).first()

    if request.method == 'POST':
        task.status = request.form['status']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your status'

    else:
        return render_template('update.html', task=task)


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, port=5050)

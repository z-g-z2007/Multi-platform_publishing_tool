from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from models import User, db
import hashlib

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('content.publish'))
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.password == hash_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': '登录成功'})
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    
    new_user = User(username=username, password=hash_password(password), email=email)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '注册成功'})

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

def init_admin():
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=hash_password('admin123'))
        db.session.add(admin)
        db.session.commit()
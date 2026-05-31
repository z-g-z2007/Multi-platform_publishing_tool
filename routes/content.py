from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from models import Material, db
import os
import uuid

content_bp = Blueprint('content', __name__)


def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@content_bp.route('/publish', methods=['GET'])
@login_required
def publish():
    return render_template('publish.html')


@content_bp.route('/api/material/upload', methods=['POST'])
@login_required
def upload_material():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + file.filename
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)

        os.makedirs(upload_folder, exist_ok=True)
        file.save(file_path)

        material = Material(
            user_id=session['user_id'],
            filename=filename,
            original_name=file.filename,
            file_path=file_path,
            file_type=file.content_type
        )
        db.session.add(material)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '上传成功',
            'material_id': material.id,
            'filename': filename,  # 返回带UUID的实际文件名
            'original_name': material.original_name
        })

    return jsonify({'success': False, 'message': '文件格式不支持'}), 400

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from config import config
import os
import logging

from models import db

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.content import content_bp
    from routes.publish import publish_bp
    from routes.records import records_bp
    from routes.dashboard import dashboard_bp
    from routes.platforms import platforms_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(publish_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(platforms_bp)

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': '接口不存在'}), 404
        return render_template('login.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': '服务器内部错误'}), 500
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500

    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return redirect(url_for('content.publish'))

    # 添加uploads目录的静态文件服务
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        upload_folder = app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        from routes.auth import init_admin
        init_admin()
    app.run(host='0.0.0.0', port=5000, debug=True)
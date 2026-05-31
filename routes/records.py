"""
发布记录路由 - 多平台发布历史、适配内容详情
"""
from flask import Blueprint, render_template, request, jsonify, session
from models import PublishTask, PlatformAdaptation
from adapters import get_platform_info
from routes.content import login_required

records_bp = Blueprint('records', __name__)


@records_bp.route('/records', methods=['GET'])
@login_required
def records():
    return render_template('records.html')


@records_bp.route('/api/records', methods=['GET'])
@login_required
def get_records():
    """获取发布记录列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    platform_filter = request.args.get('platform', None)  # 可选平台筛选
    status_filter = request.args.get('status', None)  # 可选状态筛选

    query = PublishTask.query.filter_by(user_id=session['user_id'])

    if status_filter:
        query = query.filter_by(status=status_filter)

    query = query.order_by(PublishTask.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items

    result = []
    for task in tasks:
        adaptations = PlatformAdaptation.query.filter_by(task_id=task.id)

        if platform_filter:
            adaptations = adaptations.filter_by(platform_type=platform_filter)

        adaptations = adaptations.all()

        adapt_list = []
        for adapt in adaptations:
            info = get_platform_info(adapt.platform_type)
            adapt_list.append({
                'id': adapt.id,
                'platform_type': adapt.platform_type,
                'platform_name': info.get('name', adapt.platform_type) if info else adapt.platform_type,
                'platform_icon': info.get('icon', '📄') if info else '📄',
                'publish_status': adapt.publish_status,
                'retry_count': adapt.retry_count,
                'max_retry': adapt.max_retry,
                'error_message': adapt.error_message,
                'can_retry': adapt.can_retry() and adapt.publish_status == 'failed',
                'published_at': adapt.published_at.isoformat() if adapt.published_at else None
            })

        result.append({
            'id': task.id,
            'original_title': task.original_title,
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'adaptations': adapt_list
        })

    return jsonify({
        'success': True,
        'data': result,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@records_bp.route('/api/records/<int:task_id>', methods=['GET'])
@login_required
def get_record_detail(task_id):
    """获取单条发布记录详情（含适配前后对比）"""
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()
    adapt_list = []
    for adapt in adaptations:
        info = get_platform_info(adapt.platform_type)
        adapt_list.append({
            'id': adapt.id,
            'platform_type': adapt.platform_type,
            'platform_name': info.get('name', adapt.platform_type) if info else adapt.platform_type,
            'platform_icon': info.get('icon', '📄') if info else '📄',
            'adapted_title': adapt.adapted_title,
            'adapted_content': adapt.adapted_content,
            'original_title': adapt.original_title,
            'original_content': adapt.original_content,
            'publish_status': adapt.publish_status,
            'retry_count': adapt.retry_count,
            'max_retry': adapt.max_retry,
            'can_retry': adapt.can_retry() and adapt.publish_status == 'failed',
            'error_message': adapt.error_message,
            'published_at': adapt.published_at.isoformat() if adapt.published_at else None,
            'created_at': adapt.created_at.isoformat() if adapt.created_at else None,
            'updated_at': adapt.updated_at.isoformat() if adapt.updated_at else None
        })

    return jsonify({
        'success': True,
        'data': {
            'id': task.id,
            'original_title': task.original_title,
            'original_content': task.original_content,
            'selected_platforms': task.selected_platforms.split(',') if task.selected_platforms else [],
            'status': task.status,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
            'adaptations': adapt_list
        }
    })

"""
数据看板路由 - 多平台分发数据统计与可视化
"""
from flask import Blueprint, render_template, jsonify, session
from models import PublishTask, PlatformAdaptation
from adapters import get_all_platforms, get_platform_info
from routes.content import login_required
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


def _get_db():
    """延迟获取 db 实例，避免循环导入"""
    from app import db
    return db


@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@login_required
def get_stats():
    """获取数据看板统计数据"""
    user_id = session['user_id']

    # 任务总数
    total_tasks = PublishTask.query.filter_by(user_id=user_id).count()

    # 各状态任务数
    status_counts = db_query_status_counts(user_id)

    # 平台统计（动态获取所有已注册平台）
    all_platforms = get_all_platforms()
    platform_stats = {}

    for p_info in all_platforms:
        ptype = p_info['type']
        adaptations = PlatformAdaptation.query.join(
            PublishTask
        ).filter(
            PublishTask.user_id == user_id,
            PlatformAdaptation.platform_type == ptype
        ).all()

        total = len(adaptations)
        success = len([a for a in adaptations if a.publish_status == 'success'])
        failed = len([a for a in adaptations if a.publish_status == 'failed'])
        pending = len([a for a in adaptations if a.publish_status == 'pending'])
        publishing = len([a for a in adaptations if a.publish_status == 'publishing'])
        success_rate = round(success / total * 100, 1) if total > 0 else 0

        # 平均重试次数
        total_retries = sum(a.retry_count for a in adaptations)
        avg_retry = round(total_retries / total, 2) if total > 0 else 0

        platform_stats[ptype] = {
            'name': p_info['name'],
            'icon': p_info['icon'],
            'color': p_info.get('color', '#666'),
            'total': total,
            'success': success,
            'failed': failed,
            'pending': pending,
            'publishing': publishing,
            'success_rate': success_rate,
            'avg_retry': avg_retry
        }

    # 总统计
    total_adaptations = sum(platform_stats[p]['total'] for p in platform_stats)
    total_success = sum(platform_stats[p]['success'] for p in platform_stats)
    total_failed = sum(platform_stats[p]['failed'] for p in platform_stats)

    # 图表数据
    chart_data = []
    for ptype, stats in platform_stats.items():
        if stats['total'] > 0:
            chart_data.append({
                'platform': stats['name'],
                'icon': stats['icon'],
                'color': stats['color'],
                'success': stats['success'],
                'failed': stats['failed'],
                'total': stats['total']
            })

    # 整体成功率
    overall_success_rate = round(total_success / total_adaptations * 100, 1) if total_adaptations > 0 else 0

    # 最近发布记录（最近10条）
    recent_tasks = PublishTask.query.filter_by(user_id=user_id) \
        .order_by(PublishTask.created_at.desc()).limit(10).all()

    recent_list = []
    for task in recent_tasks:
        adaptations = PlatformAdaptation.query.filter_by(task_id=task.id).all()
        recent_list.append({
            'id': task.id,
            'title': task.original_title[:30] + ('...' if len(task.original_title) > 30 else ''),
            'status': task.status,
            'platforms_count': len(adaptations),
            'created_at': task.created_at.isoformat() if task.created_at else None
        })

    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'total_tasks': total_tasks,
                'total_adaptations': total_adaptations,
                'total_success': total_success,
                'total_failed': total_failed,
                'overall_success_rate': overall_success_rate,
                'status_breakdown': status_counts
            },
            'platform_stats': platform_stats,
            'chart_data': chart_data,
            'recent_tasks': recent_list
        }
    })


def db_query_status_counts(user_id):
    """查询各状态任务数"""
    db = _get_db()
    results = db.session.query(
        PublishTask.status, func.count(PublishTask.id)
    ).filter(
        PublishTask.user_id == user_id
    ).group_by(PublishTask.status).all()

    counts = {
        'pending': 0,
        'processing': 0,
        'partial': 0,
        'success': 0,
        'failed': 0
    }
    for status, count in results:
        if status in counts:
            counts[status] = count

    return counts

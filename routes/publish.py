"""
发布路由 - 核心业务模块
- 内容统一接收
- 多平台格式适配
- 多平台批量模拟发布
- 单平台独立重试
- 全局异常处理
"""
from flask import Blueprint, request, jsonify, session
from models import PublishTask, PlatformAdaptation, OperationLog, db
from adapters import get_adapter, get_all_platforms, get_platform_info
from routes.content import login_required
import random
import time
import json
import logging
from datetime import datetime

publish_bp = Blueprint('publish', __name__)
logger = logging.getLogger(__name__)


def _log_operation(user_id, operation, status, message, task_id=None, platform_type=None, detail=None):
    """统一操作日志记录"""
    try:
        log = OperationLog(
            user_id=user_id,
            task_id=task_id,
            platform_type=platform_type,
            operation=operation,
            status=status,
            message=message,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f'日志记录失败: {e}')


def _update_task_status(task):
    """根据子任务状态更新主任务状态"""
    adaptations = PlatformAdaptation.query.filter_by(task_id=task.id).all()
    if not adaptations:
        return

    statuses = [a.publish_status for a in adaptations]
    all_success = all(s == 'success' for s in statuses)
    all_failed = all(s == 'failed' for s in statuses)
    has_pending = any(s == 'pending' for s in statuses)
    has_publishing = any(s == 'publishing' for s in statuses)

    if has_publishing:
        task.status = 'processing'
    elif has_pending:
        task.status = 'pending'
    elif all_success:
        task.status = 'success'
    elif all_failed:
        task.status = 'failed'
    else:
        task.status = 'partial'

    db.session.commit()


@publish_bp.route('/api/platforms', methods=['GET'])
def get_platforms():
    """获取所有已注册的平台信息"""
    platforms = get_all_platforms()
    return jsonify({'success': True, 'data': platforms})


@publish_bp.route('/api/adapt', methods=['POST'])
@login_required
def adapt_content():
    """
    多平台格式适配接口
    接收原始内容，根据勾选平台批量生成适配结果
    单个平台适配失败不影响其他平台
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        platforms = data.get('platforms', [])

        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400

        if not platforms:
            return jsonify({'success': False, 'message': '请选择至少一个平台'}), 400

        results = []
        errors = []

        for platform in platforms:
            try:
                adapter_class = get_adapter(platform)
                if adapter_class:
                    adapter = adapter_class()
                    result = adapter.adapt(title, content)
                    results.append(result)
                    _log_operation(
                        session['user_id'], 'adapt', 'success',
                        f'{result["platform_name"]} 适配成功',
                        platform_type=platform,
                        detail={'title_length': result['title_length'],
                                'content_length': result['content_length']}
                    )
                else:
                    # 未注册的平台也返回基本信息
                    info = get_platform_info(platform)
                    results.append({
                        'platform_type': platform,
                        'platform_name': info.get('name', platform) if info else platform,
                        'platform_icon': info.get('icon', '📄') if info else '📄',
                        'adapted_title': title,
                        'adapted_content': content,
                        'tags': [],
                        'style_rules': {},
                        'title_length': len(title),
                        'content_length': len(content)
                    })
                    _log_operation(
                        session['user_id'], 'adapt', 'warning',
                        f'平台 {platform} 未注册适配器，使用原始内容',
                        platform_type=platform
                    )
            except Exception as e:
                logger.error(f'平台 {platform} 适配失败: {e}')
                errors.append({'platform': platform, 'error': str(e)})
                _log_operation(
                    session['user_id'], 'adapt', 'error',
                    f'{platform} 适配失败: {str(e)}',
                    platform_type=platform
                )

        return jsonify({
            'success': True,
            'data': results,
            'errors': errors if errors else None,
            'total_platforms': len(platforms),
            'success_count': len(results)
        })

    except Exception as e:
        logger.error(f'适配接口异常: {e}')
        return jsonify({'success': False, 'message': f'适配失败: {str(e)}'}), 500


@publish_bp.route('/api/publish', methods=['POST'])
@login_required
def create_publish_task():
    """
    创建发布任务
    保存原始内容，为每个选中平台创建适配记录
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        platforms = data.get('platforms', [])

        if not title or not content:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400

        if not platforms:
            return jsonify({'success': False, 'message': '请选择至少一个平台'}), 400

        # 创建主任务
        task = PublishTask(
            user_id=session['user_id'],
            original_title=title,
            original_content=content,
            selected_platforms=','.join(platforms),
            status='pending'
        )
        db.session.add(task)
        db.session.commit()

        # 为每个平台创建适配记录
        adaptation_count = 0
        for platform in platforms:
            try:
                adapter_class = get_adapter(platform)
                if adapter_class:
                    adapter = adapter_class()
                    adapted = adapter.adapt(title, content)
                    adaptation = PlatformAdaptation(
                        task_id=task.id,
                        platform_type=platform,
                        adapted_title=adapted['adapted_title'],
                        adapted_content=adapted['adapted_content'],
                        original_title=title,
                        original_content=content,
                        publish_status='pending'
                    )
                else:
                    adaptation = PlatformAdaptation(
                        task_id=task.id,
                        platform_type=platform,
                        adapted_title=title,
                        adapted_content=content,
                        original_title=title,
                        original_content=content,
                        publish_status='pending'
                    )
                db.session.add(adaptation)
                adaptation_count += 1
            except Exception as e:
                logger.error(f'创建平台 {platform} 适配记录失败: {e}')
                _log_operation(
                    session['user_id'], 'adapt', 'error',
                    f'创建 {platform} 适配记录失败: {str(e)}',
                    task_id=task.id, platform_type=platform
                )

        db.session.commit()

        _log_operation(
            session['user_id'], 'publish', 'success',
            f'发布任务创建成功，包含 {adaptation_count} 个平台',
            task_id=task.id
        )

        return jsonify({
            'success': True,
            'task_id': task.id,
            'message': f'任务创建成功，共 {adaptation_count} 个平台',
            'platform_count': adaptation_count
        })

    except Exception as e:
        logger.error(f'创建发布任务失败: {e}')
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建任务失败: {str(e)}'}), 500


@publish_bp.route('/api/publish/execute/<int:task_id>', methods=['POST'])
@login_required
def execute_publish(task_id):
    """
    执行批量发布
    对每个平台独立模拟发布，互不影响
    支持实时状态推送
    """
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()

    if not adaptations:
        return jsonify({'success': False, 'message': '没有可发布的平台'}), 400

    # 逐个平台执行发布（模拟）
    results = []
    for adaptation in adaptations:
        try:
            # 更新状态为发布中
            adaptation.publish_status = 'publishing'
            db.session.commit()

            # 模拟发布耗时
            time.sleep(random.uniform(0.3, 1.0))

            # 模拟发布结果（70%成功率）
            success = random.random() < 0.7

            if success:
                adaptation.publish_status = 'success'
                adaptation.published_at = datetime.utcnow()
                results.append({
                    'platform': adaptation.platform_type,
                    'status': 'success',
                    'message': '发布成功'
                })
                _log_operation(
                    session['user_id'], 'publish', 'success',
                    f'{adaptation.platform_type} 发布成功',
                    task_id=task_id, platform_type=adaptation.platform_type
                )
            else:
                error_msgs = [
                    '网络超时，请稍后重试',
                    '平台API限流，请稍后重试',
                    '内容审核未通过',
                    '服务器繁忙，请稍后重试',
                ]
                error_msg = random.choice(error_msgs)
                adaptation.publish_status = 'failed'
                adaptation.error_message = error_msg
                results.append({
                    'platform': adaptation.platform_type,
                    'status': 'failed',
                    'message': error_msg
                })
                _log_operation(
                    session['user_id'], 'publish', 'error',
                    f'{adaptation.platform_type} 发布失败: {error_msg}',
                    task_id=task_id, platform_type=adaptation.platform_type,
                    detail={'error': error_msg}
                )

            db.session.commit()

        except Exception as e:
            logger.error(f'平台 {adaptation.platform_type} 发布异常: {e}')
            adaptation.publish_status = 'failed'
            adaptation.error_message = f'系统异常: {str(e)}'
            db.session.commit()
            results.append({
                'platform': adaptation.platform_type,
                'status': 'failed',
                'message': f'系统异常: {str(e)}'
            })
            _log_operation(
                session['user_id'], 'publish', 'error',
                f'{adaptation.platform_type} 发布异常: {str(e)}',
                task_id=task_id, platform_type=adaptation.platform_type
            )

    # 更新主任务状态
    _update_task_status(task)

    success_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len([r for r in results if r['status'] == 'failed'])

    return jsonify({
        'success': True,
        'message': f'发布完成：成功 {success_count}，失败 {failed_count}',
        'task_status': task.status,
        'results': results,
        'summary': {
            'total': len(results),
            'success': success_count,
            'failed': failed_count
        }
    })


@publish_bp.route('/api/publish/retry/<int:adaptation_id>', methods=['POST'])
@login_required
def retry_publish(adaptation_id):
    """
    单平台独立重试发布
    某个平台失败不影响其他平台
    """
    adaptation = PlatformAdaptation.query.get(adaptation_id)

    if not adaptation:
        return jsonify({'success': False, 'message': '适配记录不存在'}), 404

    task = PublishTask.query.get(adaptation.task_id)
    if not task or task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    # 检查重试次数
    if not adaptation.can_retry():
        return jsonify({
            'success': False,
            'message': f'已达到最大重试次数（{adaptation.max_retry}次）'
        }), 400

    # 只有失败状态才能重试
    if adaptation.publish_status not in ('failed',):
        return jsonify({
            'success': False,
            'message': f'当前状态 {adaptation.publish_status} 不允许重试'
        }), 400

    try:
        # 更新为重试中
        adaptation.publish_status = 'publishing'
        adaptation.retry_count += 1
        adaptation.error_message = None
        db.session.commit()

        # 模拟重试耗时
        time.sleep(random.uniform(0.5, 1.0))

        # 重试成功率更高（85%）
        success = random.random() < 0.85

        if success:
            adaptation.publish_status = 'success'
            adaptation.published_at = datetime.utcnow()
            _log_operation(
                session['user_id'], 'retry', 'success',
                f'{adaptation.platform_type} 第{adaptation.retry_count}次重试成功',
                task_id=task.id, platform_type=adaptation.platform_type
            )
        else:
            error_msgs = [
                '重试仍然失败：网络不稳定',
                '重试仍然失败：平台暂时不可用',
            ]
            error_msg = random.choice(error_msgs)
            adaptation.publish_status = 'failed'
            adaptation.error_message = error_msg
            _log_operation(
                session['user_id'], 'retry', 'error',
                f'{adaptation.platform_type} 第{adaptation.retry_count}次重试失败',
                task_id=task.id, platform_type=adaptation.platform_type
            )

        db.session.commit()

        # 更新主任务状态
        _update_task_status(task)

        return jsonify({
            'success': True,
            'message': '重试完成',
            'publish_status': adaptation.publish_status,
            'retry_count': adaptation.retry_count,
            'error_message': adaptation.error_message,
            'task_status': task.status
        })

    except Exception as e:
        logger.error(f'重试发布异常: {e}')
        adaptation.publish_status = 'failed'
        adaptation.error_message = f'重试异常: {str(e)}'
        db.session.commit()
        return jsonify({'success': False, 'message': f'重试失败: {str(e)}'}), 500


@publish_bp.route('/api/publish/status/<int:task_id>', methods=['GET'])
@login_required
def get_publish_status(task_id):
    """获取发布任务的实时状态"""
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()

    platform_statuses = []
    for a in adaptations:
        info = get_platform_info(a.platform_type)
        platform_statuses.append({
            'adaptation_id': a.id,
            'platform_type': a.platform_type,
            'platform_name': info.get('name', a.platform_type) if info else a.platform_type,
            'platform_icon': info.get('icon', '📄') if info else '📄',
            'publish_status': a.publish_status,
            'retry_count': a.retry_count,
            'error_message': a.error_message,
        })

    return jsonify({
        'success': True,
        'data': {
            'task_id': task.id,
            'task_status': task.status,
            'platforms': platform_statuses
        }
    })

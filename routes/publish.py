"""
发布路由 - 核心业务模块（简化版）
- 内容统一接收
- 多平台格式适配
- 多平台批量模拟发布
- 单平台独立重试
- 实时进度推送（SSE）
- 全局异常处理
"""
from flask import Blueprint, request, jsonify, session, Response, stream_with_context
from models import PublishTask, PlatformAdaptation, OperationLog, db
from adapters import get_adapter, get_all_platforms, get_platform_info
from routes.content import login_required
import random
import time
import json
import logging
from datetime import datetime
from threading import Thread

publish_bp = Blueprint('publish', __name__)
logger = logging.getLogger(__name__)


# 错误消息池
ERROR_MESSAGES = {
    'network': [
        '网络超时，请稍后重试',
        '网络连接不稳定',
        '服务器响应超时',
        'DNS解析失败',
        '连接被拒绝'
    ],
    'api': [
        '平台API限流，请稍后重试',
        'API调用次数超限',
        '接口维护中，请稍后尝试',
        'token过期，请重新登录'
    ],
    'content': [
        '内容审核未通过',
        '内容包含敏感信息',
        '标题不符合规范',
        '图片格式不支持',
        '视频时长超限'
    ],
    'system': [
        '服务器繁忙，请稍后重试',
        '系统维护中',
        '服务暂时不可用',
        '内部错误，请联系管理员'
    ]
}

# 违规词语列表（示例）
VIOLATION_WORDS = [
    '色情', '暴力', '赌博', '毒品', '诈骗', '反动', '恐怖',
    '造谣', '辱骂', '人身攻击', '恶意诋毁', '虚假宣传',
    '政治敏感', '宗教极端', '民族仇恨', '地域歧视', '性别歧视'
]


def _get_random_error(error_type='network'):
    """获取随机错误消息"""
    messages = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['network'])
    return random.choice(messages)


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


def _extract_content(data):
    """
    提取内容数据
    支持两种格式：
    1. 字符串格式：直接返回字符串
    2. 对象格式：包含text、html、images字段的图文混排内容
    """
    content = data.get('content', '')
    
    if isinstance(content, dict):
        # 新的图文混排格式
        return content.get('text', '').strip(), content.get('html', ''), content.get('images', [])
    else:
        # 旧的纯文本格式
        return str(content).strip(), '', []


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
    支持图文混排内容
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content_text, content_html, content_images = _extract_content(data)
        platforms = data.get('platforms', [])

        if not title or not content_text:
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
                    # 传递完整内容信息给适配器
                    result = adapter.adapt(title, content_text, content_images)
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
                        'adapted_content': content_text,
                        'tags': [],
                        'style_rules': {},
                        'title_length': len(title),
                        'content_length': len(content_text)
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
    支持图文混排内容
    """
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content_text, content_html, content_images = _extract_content(data)
        platforms = data.get('platforms', [])

        if not title or not content_text:
            return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400

        if not platforms:
            return jsonify({'success': False, 'message': '请选择至少一个平台'}), 400

        # 创建主任务（保存完整内容信息）
        content_info = {
            'text': content_text,
            'html': content_html,
            'images': content_images
        }
        
        task = PublishTask(
            user_id=session['user_id'],
            original_title=title,
            original_content=json.dumps(content_info, ensure_ascii=False),
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
                    adapted = adapter.adapt(title, content_text, content_images)
                    adaptation = PlatformAdaptation(
                        task_id=task.id,
                        platform_type=platform,
                        adapted_title=adapted['adapted_title'],
                        adapted_content=adapted['adapted_content'],
                        original_title=title,
                        original_content=json.dumps(content_info, ensure_ascii=False),
                        publish_status='pending'
                    )
                else:
                    adaptation = PlatformAdaptation(
                        task_id=task.id,
                        platform_type=platform,
                        adapted_title=title,
                        adapted_content=content_text,
                        original_title=title,
                        original_content=json.dumps(content_info, ensure_ascii=False),
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


def _check_violation(content):
    """
    检查内容是否包含违规词语
    :param content: 要检查的内容
    :return: (has_violation, violation_word)
    """
    for word in VIOLATION_WORDS:
        if word in content:
            return True, word
    return False, None


def _simulate_publish(adaptation):
    """
    模拟单个平台发布
    默认总是成功，只有检测到违规词语时才失败
    :param adaptation: PlatformAdaptation对象
    :return: (success, message)
    """
    # 模拟网络延迟
    delay = random.uniform(0.3, 1.0)
    time.sleep(delay)

    # 检查标题和内容是否包含违规词语
    content_to_check = adaptation.adapted_title + ' ' + adaptation.adapted_content
    has_violation, violation_word = _check_violation(content_to_check)

    if has_violation:
        # 检测到违规词语，发布失败
        return False, f'内容审核未通过，包含敏感信息「{violation_word}」'
    else:
        # 无违规内容，发布成功
        return True, '发布成功'


def _execute_publish_worker(task_id):
    """
    发布工作线程
    执行实际的发布操作
    """
    try:
        task = PublishTask.query.get(task_id)
        if not task:
            return

        adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()
        
        for adaptation in adaptations:
            if adaptation.publish_status != 'pending':
                continue

            # 更新状态为发布中
            adaptation.publish_status = 'publishing'
            db.session.commit()

            # 执行模拟发布
            success, message = _simulate_publish(adaptation)

            if success:
                adaptation.publish_status = 'success'
                adaptation.published_at = datetime.utcnow()
                
                _log_operation(
                    task.user_id, 'publish', 'success',
                    f'{adaptation.platform_type} 发布成功',
                    task_id=task_id, platform_type=adaptation.platform_type
                )
            else:
                adaptation.publish_status = 'failed'
                adaptation.error_message = message
                
                _log_operation(
                    task.user_id, 'publish', 'error',
                    f'{adaptation.platform_type} 发布失败: {message}',
                    task_id=task_id, platform_type=adaptation.platform_type,
                    detail={'error': message}
                )

            db.session.commit()

        # 更新主任务状态
        _update_task_status(task)

    except Exception as e:
        logger.error(f'发布工作线程异常: {e}')


@publish_bp.route('/api/publish/execute/<int:task_id>', methods=['POST'])
@login_required
def execute_publish(task_id):
    """
    执行批量发布（异步模式）
    对每个平台独立模拟发布，互不影响
    返回任务状态，客户端通过SSE获取实时进度
    """
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    if task.status in ('processing',):
        return jsonify({'success': False, 'message': '任务正在执行中'}), 400

    adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()

    if not adaptations:
        return jsonify({'success': False, 'message': '没有可发布的平台'}), 400

    # 在后台线程执行发布
    thread = Thread(
        target=_execute_publish_worker,
        args=(task_id,),
        daemon=True
    )
    thread.start()

    return jsonify({
        'success': True,
        'message': '任务已提交，开始执行发布',
        'task_id': task_id
    })


@publish_bp.route('/api/publish/progress/<int:task_id>')
@login_required
def publish_progress(task_id):
    """
    SSE实时进度推送
    客户端通过EventSource接收发布进度
    """
    def generate():
        last_status = None
        
        while True:
            task = PublishTask.query.get(task_id)
            if not task:
                yield f'data: {json.dumps({"type": "error", "message": "任务不存在"})}\n\n'
                break

            # 检查权限
            if task.user_id != session.get('user_id'):
                yield f'data: {json.dumps({"type": "error", "message": "无权访问"})}\n\n'
                break

            adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()
            
            platform_statuses = []
            for a in adaptations:
                info = get_platform_info(a.platform_type)
                platform_statuses.append({
                    'platform_type': a.platform_type,
                    'platform_name': info.get('name', a.platform_type) if info else a.platform_type,
                    'platform_icon': info.get('icon', '📄') if info else '📄',
                    'status': a.publish_status,
                    'error_message': a.error_message
                })

            current_status = {
                'type': 'progress',
                'task_id': task_id,
                'task_status': task.status,
                'platforms': platform_statuses
            }

            # 只有状态变化时才推送
            if current_status != last_status:
                last_status = current_status
                yield f'data: {json.dumps(current_status, ensure_ascii=False)}\n\n'

            # 任务完成时退出
            if task.status in ('success', 'failed', 'partial'):
                yield f'data: {json.dumps({"type": "complete", "task_id": task_id, "status": task.status})}\n\n'
                break

            time.sleep(0.5)

    return Response(stream_with_context(generate()), content_type='text/event-stream')


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
        time.sleep(random.uniform(0.3, 1.0))

        # 重试成功率更高（90%）
        success = random.random() < 0.9

        if success:
            adaptation.publish_status = 'success'
            adaptation.published_at = datetime.utcnow()
            _log_operation(
                session['user_id'], 'retry', 'success',
                f'{adaptation.platform_type} 第{adaptation.retry_count}次重试成功',
                task_id=task.id, platform_type=adaptation.platform_type
            )
        else:
            error_msg = _get_random_error('network')
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

    # 统计信息
    success_count = len([a for a in adaptations if a.publish_status == 'success'])
    failed_count = len([a for a in adaptations if a.publish_status == 'failed'])
    pending_count = len([a for a in adaptations if a.publish_status == 'pending'])

    return jsonify({
        'success': True,
        'data': {
            'task_id': task.id,
            'task_status': task.status,
            'platforms': platform_statuses,
            'summary': {
                'total': len(adaptations),
                'success': success_count,
                'failed': failed_count,
                'pending': pending_count
            }
        }
    })


@publish_bp.route('/api/publish/batch_retry/<int:task_id>', methods=['POST'])
@login_required
def batch_retry(task_id):
    """
    批量重试失败的平台
    对所有失败的平台进行重试
    """
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    failed_adaptations = PlatformAdaptation.query.filter_by(
        task_id=task_id,
        publish_status='failed'
    ).all()

    if not failed_adaptations:
        return jsonify({'success': False, 'message': '没有需要重试的平台'}), 400

    results = []
    for adaptation in failed_adaptations:
        if not adaptation.can_retry():
            results.append({
                'platform': adaptation.platform_type,
                'status': 'skipped',
                'message': f'已达到最大重试次数'
            })
            continue

        try:
            adaptation.publish_status = 'publishing'
            adaptation.retry_count += 1
            db.session.commit()

            time.sleep(random.uniform(0.3, 1.0))

            success = random.random() < 0.9

            if success:
                adaptation.publish_status = 'success'
                adaptation.published_at = datetime.utcnow()
                results.append({
                    'platform': adaptation.platform_type,
                    'status': 'success',
                    'message': '重试成功'
                })
            else:
                error_msg = _get_random_error('network')
                adaptation.publish_status = 'failed'
                adaptation.error_message = error_msg
                results.append({
                    'platform': adaptation.platform_type,
                    'status': 'failed',
                    'message': error_msg
                })

            db.session.commit()

        except Exception as e:
            adaptation.publish_status = 'failed'
            adaptation.error_message = str(e)
            db.session.commit()
            results.append({
                'platform': adaptation.platform_type,
                'status': 'failed',
                'message': f'重试异常: {str(e)}'
            })

    _update_task_status(task)

    success_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len([r for r in results if r['status'] == 'failed'])

    return jsonify({
        'success': True,
        'message': f'批量重试完成：成功 {success_count}，失败 {failed_count}',
        'results': results,
        'task_status': task.status
    })


@publish_bp.route('/api/publish/preview/<int:task_id>', methods=['GET'])
@login_required
def preview_publish(task_id):
    """
    获取发布预览内容
    返回所有平台的适配结果
    """
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    adaptations = PlatformAdaptation.query.filter_by(task_id=task_id).all()

    previews = []
    for adaptation in adaptations:
        info = get_platform_info(adaptation.platform_type)
        previews.append({
            'platform_type': adaptation.platform_type,
            'platform_name': info.get('name', adaptation.platform_type) if info else adaptation.platform_type,
            'platform_icon': info.get('icon', '📄') if info else '📄',
            'platform_color': info.get('color', '#333') if info else '#333',
            'adapted_title': adaptation.adapted_title,
            'adapted_content': adaptation.adapted_content,
            'publish_status': adaptation.publish_status,
            'preview_url': f'/api/publish/preview/{task_id}/{adaptation.platform_type}'
        })

    return jsonify({
        'success': True,
        'data': {
            'task_id': task.id,
            'original_title': task.original_title,
            'previews': previews
        }
    })


@publish_bp.route('/api/publish/preview/<int:task_id>/<platform_type>', methods=['GET'])
@login_required
def preview_single_platform(task_id, platform_type):
    """
    获取单个平台的发布预览
    """
    task = PublishTask.query.get(task_id)

    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    if task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'}), 403

    adaptation = PlatformAdaptation.query.filter_by(
        task_id=task_id,
        platform_type=platform_type
    ).first()

    if not adaptation:
        return jsonify({'success': False, 'message': '平台适配记录不存在'}), 404

    info = get_platform_info(platform_type)

    return jsonify({
        'success': True,
        'data': {
            'platform_type': platform_type,
            'platform_name': info.get('name', platform_type) if info else platform_type,
            'platform_icon': info.get('icon', '📄') if info else '📄',
            'platform_color': info.get('color', '#333') if info else '#333',
            'adapted_title': adaptation.adapted_title,
            'adapted_content': adaptation.adapted_content,
            'original_title': adaptation.original_title,
            'publish_status': adaptation.publish_status,
            'style_rules': info.get('style_rules', {}) if info else {}
        }
    })

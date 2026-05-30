"""
平台管理路由 - 提供平台信息API
"""
from flask import Blueprint, jsonify
from adapters import get_all_platforms, get_categories, get_platforms_by_category

platforms_bp = Blueprint('platforms', __name__)


@platforms_bp.route('/api/platforms', methods=['GET'])
def list_platforms():
    """
    获取所有已注册平台列表
    """
    try:
        platforms = get_all_platforms()
        categories = get_categories()

        return jsonify({
            'success': True,
            'platforms': platforms,
            'categories': categories,
            'total': len(platforms)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@platforms_bp.route('/api/platforms/<platform_type>', methods=['GET'])
def get_platform(platform_type):
    """
    获取单个平台信息
    """
    try:
        from adapters import get_platform_info
        info = get_platform_info(platform_type)

        if info:
            return jsonify({
                'success': True,
                'platform': info
            })
        else:
            return jsonify({
                'success': False,
                'message': '平台不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@platforms_bp.route('/api/platforms/category/<category>', methods=['GET'])
def list_platforms_by_category(category):
    """
    按分类获取平台列表
    """
    try:
        platforms = get_platforms_by_category(category)

        return jsonify({
            'success': True,
            'category': category,
            'platforms': platforms,
            'total': len(platforms)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@platforms_bp.route('/api/platforms/categories', methods=['GET'])
def list_categories():
    """
    获取所有平台分类
    """
    try:
        categories = get_categories()

        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

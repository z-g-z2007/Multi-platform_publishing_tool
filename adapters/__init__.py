"""
平台适配器注册中心 - 插件化可插拔架构
新增平台只需在此注册即可，核心代码零侵入
"""
from .xiaohongshu_adapter import XiaohongshuAdapter
from .wechat_adapter import WechatAdapter
from .zhihu_adapter import ZhihuAdapter
from .bilibili_adapter import BilibiliAdapter

# 适配器注册表：新增平台在此添加一行即可
ADAPTER_REGISTRY = {
    'xiaohongshu': XiaohongshuAdapter,
    'wechat': WechatAdapter,
    'zhihu': ZhihuAdapter,
    'bilibili': BilibiliAdapter,
    # 扩展示例：
    # 'douyin': DouyinAdapter,       # 抖音
    # 'weibo': WeiboAdapter,         # 微博
    # 'baijiahao': BaijiahaoAdapter, # 百家号
}

# 平台信息列表（供前端使用）
PLATFORM_INFO = {
    'xiaohongshu': {
        'type': 'xiaohongshu',
        'name': '小红书',
        'icon': '📕',
        'description': '图文笔记风格，短平快，适合手机阅读',
        'color': '#FF2442'
    },
    'wechat': {
        'type': 'wechat',
        'name': '微信公众号',
        'icon': '💬',
        'description': '正式长文风格，排版工整，适合深度阅读',
        'color': '#07C160'
    },
    'zhihu': {
        'type': 'zhihu',
        'name': '知乎',
        'icon': '💡',
        'description': '干货正式文风，内容严谨，适合知识分享',
        'color': '#0066FF'
    },
    'bilibili': {
        'type': 'bilibili',
        'name': 'B站',
        'icon': '📺',
        'description': '视频简介风格，简洁清爽，适合UP主发布',
        'color': '#FB7299'
    },
}


def get_adapter(platform_type: str):
    """获取平台适配器类（工厂方法）"""
    return ADAPTER_REGISTRY.get(platform_type)


def get_all_platforms() -> list:
    """获取所有已注册的平台信息"""
    return list(PLATFORM_INFO.values())


def get_platform_info(platform_type: str) -> dict:
    """获取单个平台信息"""
    return PLATFORM_INFO.get(platform_type, {})


def register_adapter(platform_type: str, adapter_class, platform_info: dict = None):
    """
    动态注册新平台适配器（扩展接口）
    示例：
        register_adapter('douyin', DouyinAdapter, {
            'type': 'douyin', 'name': '抖音', 'icon': '🎵', ...
        })
    """
    ADAPTER_REGISTRY[platform_type] = adapter_class
    if platform_info:
        PLATFORM_INFO[platform_type] = platform_info

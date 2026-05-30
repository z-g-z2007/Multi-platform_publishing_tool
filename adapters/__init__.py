"""
平台适配器注册中心 - 基于插件化架构
新增平台只需添加新的 adapter 文件并实现 PlatformPluginInterface 接口
"""
from .plugin_manager import (
    PluginManager,
    PluginRegistry,
    get_plugin_manager,
    get_adapter as _get_adapter,
    get_all_platforms as _get_all_platforms,
    get_platform_info as _get_platform_info,
    register_plugin
)

# 初始化插件管理器
plugin_manager = PluginManager()
plugin_manager.register_core_plugins()

def get_adapter(platform_type: str):
    """获取平台适配器实例（工厂方法）"""
    return _get_adapter(platform_type)


def get_all_platforms() -> list:
    """获取所有已注册的平台信息列表"""
    return [p.to_dict() for p in _get_all_platforms()]


def get_platform_info(platform_type: str) -> dict:
    """获取单个平台信息"""
    info = _get_platform_info(platform_type)
    return info.to_dict() if info else {}


def get_platforms_by_category(category: str) -> list:
    """按分类获取平台列表"""
    return [p.to_dict() for p in plugin_manager.get_platforms_by_category(category)]


def get_categories() -> list:
    """获取所有平台分类"""
    return plugin_manager.registry.get_categories()


def adapt_content(platform_type: str, title: str, content: str, images: list = None) -> dict:
    """快捷方法：直接适配内容到指定平台"""
    result = plugin_manager.adapt_content(platform_type, title, content, images)
    return result.to_dict() if result else None


# 向后兼容的导出（保持原有接口）
from .xiaohongshu_adapter import XiaohongshuAdapter
from .wechat_adapter import WechatAdapter
from .zhihu_adapter import ZhihuAdapter
from .bilibili_adapter import BilibiliAdapter

# 扩展示例：导入但不自动注册（用户可按需启用）
try:
    from .weibo_adapter import WeiboAdapter
except ImportError:
    WeiboAdapter = None

try:
    from .douyin_adapter import DouyinAdapter
except ImportError:
    DouyinAdapter = None

try:
    from .toutiao_adapter import ToutiaoAdapter
except ImportError:
    ToutiaoAdapter = None

try:
    from .baijiahao_adapter import BaijiahaoAdapter
except ImportError:
    BaijiahaoAdapter = None

try:
    from .kuaishou_adapter import KuaishouAdapter
except ImportError:
    KuaishouAdapter = None

try:
    from .douban_adapter import DoubanAdapter
except ImportError:
    DoubanAdapter = None


def register_all_plugins():
    """注册所有可用插件（包括扩展插件）"""
    plugins_to_register = [
        XiaohongshuAdapter,
        WechatAdapter,
        ZhihuAdapter,
        BilibiliAdapter,
    ]

    # 添加扩展插件（如果可用）
    for adapter in [WeiboAdapter, DouyinAdapter, ToutiaoAdapter,
                    BaijiahaoAdapter, KuaishouAdapter, DoubanAdapter]:
        if adapter is not None:
            plugins_to_register.append(adapter)

    for plugin in plugins_to_register:
        try:
            register_plugin(plugin)
        except Exception as e:
            print(f'注册插件失败 {plugin.__name__}: {e}')

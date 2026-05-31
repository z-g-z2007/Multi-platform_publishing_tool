"""
平台插件管理器 - 实现插件的自动发现、注册和加载
"""
import os
import importlib
import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from .plugin_interface import PlatformPluginInterface, PlatformInfo, AdaptedContent

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    插件注册表 - 核心数据结构
    负责管理所有已注册的平台插件
    """

    def __init__(self):
        self._adapters: Dict[str, Type[PlatformPluginInterface]] = {}
        self._platforms: Dict[str, PlatformInfo] = {}
        self._categories: Dict[str, List[str]] = {}  # category -> [platform_types]

    def register(self, plugin_class: Type[PlatformPluginInterface]) -> None:
        """注册插件"""
        try:
            instance = plugin_class()
            info = instance.platform_info

            self._adapters[info.type] = plugin_class
            self._platforms[info.type] = info

            # 按分类管理
            category = info.category
            if category not in self._categories:
                self._categories[category] = []
            if info.type not in self._categories[category]:
                self._categories[category].append(info.type)

            logger.info(f'插件注册成功: {info.name} ({info.type})')
        except Exception as e:
            logger.error(f'插件注册失败: {plugin_class.__name__}, 错误: {e}')
            raise

    def unregister(self, platform_type: str) -> bool:
        """注销插件"""
        if platform_type in self._adapters:
            plugin_class = self._adapters.pop(platform_type)
            info = self._platforms.pop(platform_type)

            # 从分类中移除
            category = info.category
            if category in self._categories and platform_type in self._categories[category]:
                self._categories[category].remove(platform_type)

            logger.info(f'插件已注销: {info.name} ({platform_type})')
            return True
        return False

    def get_adapter(self, platform_type: str) -> Optional[PlatformPluginInterface]:
        """获取插件实例"""
        plugin_class = self._adapters.get(platform_type)
        if plugin_class:
            return plugin_class()
        return None

    def get_adapter_class(self, platform_type: str) -> Optional[Type[PlatformPluginInterface]]:
        """获取插件类"""
        return self._adapters.get(platform_type)

    def get_platform_info(self, platform_type: str) -> Optional[PlatformInfo]:
        """获取平台信息"""
        return self._platforms.get(platform_type)

    def get_all_platforms(self) -> List[PlatformInfo]:
        """获取所有平台信息"""
        return list(self._platforms.values())

    def get_platforms_by_category(self, category: str) -> List[PlatformInfo]:
        """获取指定分类的所有平台"""
        platform_types = self._categories.get(category, [])
        return [self._platforms[pt] for pt in platform_types if pt in self._platforms]

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self._categories.keys())

    def is_registered(self, platform_type: str) -> bool:
        """检查平台是否已注册"""
        return platform_type in self._adapters

    @property
    def platform_count(self) -> int:
        """已注册平台数量"""
        return len(self._adapters)


class PluginDiscoverer:
    """
    插件自动发现器 - 从指定目录自动扫描和加载插件
    """

    def __init__(self, plugin_dir: str = None):
        if plugin_dir is None:
            plugin_dir = os.path.dirname(__file__)
        self.plugin_dir = Path(plugin_dir)

    def discover_plugins(self) -> List[Type[PlatformPluginInterface]]:
        """
        自动发现插件
        扫描 adapter 目录下所有 *_adapter.py 文件
        """
        plugins = []
        adapter_files = self.plugin_dir.glob('*_adapter.py')

        for file_path in adapter_files:
            if file_path.name == 'base_adapter.py':
                continue

            try:
                module_name = f'adapters.{file_path.stem}'
                module = importlib.import_module(module_name)

                # 查找模块中所有 PlatformPluginInterface 的子类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, PlatformPluginInterface) and
                        attr is not PlatformPluginInterface):

                        plugins.append(attr)
                        logger.debug(f'发现插件: {attr_name}')

            except Exception as e:
                logger.error(f'加载插件失败 {file_path}: {e}')

        return plugins


class PluginManager:
    """
    插件管理器 - 统一入口
    负责插件的自动发现、注册和懒加载
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.registry = PluginRegistry()
        self.discoverer = PluginDiscoverer()
        self._initialized = True

    def register_core_plugins(self):
        """注册核心插件（内置平台）"""
        from .xiaohongshu_adapter import XiaohongshuAdapter
        from .wechat_adapter import WechatAdapter
        from .zhihu_adapter import ZhihuAdapter
        from .bilibili_adapter import BilibiliAdapter

        self.registry.register(XiaohongshuAdapter)
        self.registry.register(WechatAdapter)
        self.registry.register(ZhihuAdapter)
        self.registry.register(BilibiliAdapter)

    def auto_discover(self):
        """自动发现并注册所有插件"""
        plugins = self.discoverer.discover_plugins()
        for plugin in plugins:
            try:
                self.registry.register(plugin)
            except Exception as e:
                logger.error(f'自动注册插件失败: {plugin.__name__}, {e}')

    def register_plugin(self, plugin_class: Type[PlatformPluginInterface]):
        """手动注册插件"""
        self.registry.register(plugin_class)

    def unregister_plugin(self, platform_type: str):
        """注销插件"""
        self.registry.unregister(platform_type)

    def get_adapter(self, platform_type: str) -> Optional[PlatformPluginInterface]:
        """获取平台适配器实例"""
        return self.registry.get_adapter(platform_type)

    def get_all_platforms(self) -> List[PlatformInfo]:
        """获取所有已注册平台信息"""
        return self.registry.get_all_platforms()

    def get_platform_info(self, platform_type: str) -> Optional[PlatformInfo]:
        """获取平台信息"""
        return self.registry.get_platform_info(platform_type)

    def get_platforms_by_category(self, category: str) -> List[PlatformInfo]:
        """按分类获取平台"""
        return self.registry.get_platforms_by_category(category)

    def adapt_content(self, platform_type: str, title: str, content: str,
                     images: List[Dict] = None) -> Optional[AdaptedContent]:
        """
        统一适配接口
        :param platform_type: 平台类型
        :param title: 原始标题
        :param content: 原始正文
        :param images: 图片列表
        :return: AdaptedContent 或 None
        """
        adapter = self.get_adapter(platform_type)
        if adapter:
            return adapter.adapt(title, content, images)
        return None

    def batch_adapt(self, platform_types: List[str], title: str, content: str,
                    images: List[Dict] = None) -> Dict[str, AdaptedContent]:
        """
        批量适配内容到多个平台
        :return: {platform_type: AdaptedContent}
        """
        results = {}
        for pt in platform_types:
            adapted = self.adapt_content(pt, title, content, images)
            if adapted:
                results[pt] = adapted
        return results

    @property
    def platform_count(self) -> int:
        """已注册平台数量"""
        return self.registry.platform_count


# 全局单例
plugin_manager = PluginManager()


def get_plugin_manager() -> PluginManager:
    """获取插件管理器实例"""
    return plugin_manager


def get_adapter(platform_type: str) -> Optional[PlatformPluginInterface]:
    """快捷方法：获取适配器"""
    return plugin_manager.get_adapter(platform_type)


def get_all_platforms() -> List[PlatformInfo]:
    """快捷方法：获取所有平台"""
    return plugin_manager.get_all_platforms()


def get_platform_info(platform_type: str) -> Optional[PlatformInfo]:
    """快捷方法：获取平台信息"""
    return plugin_manager.get_platform_info(platform_type)


def register_plugin(plugin_class: Type[PlatformPluginInterface]):
    """快捷方法：注册插件"""
    plugin_manager.register_plugin(plugin_class)

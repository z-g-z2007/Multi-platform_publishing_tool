"""
平台适配器基类 - 定义统一接口
所有平台适配器继承此类，实现各自平台的差异化适配逻辑
"""
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """平台适配器基类"""
    platform_name = ''       # 平台中文名
    platform_type = ''       # 平台英文标识
    title_max_length = 100   # 标题最大字数
    content_max_length = 0   # 正文最大字数（0表示不限制）
    platform_icon = ''       # 平台图标emoji
    platform_description = ''  # 平台描述

    def adapt_title(self, title: str) -> str:
        """适配标题：各平台可重写"""
        title = title.strip()
        if self.title_max_length > 0 and len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str) -> str:
        """适配正文：各平台必须实现"""
        return content.strip()

    def get_tags(self) -> list:
        """获取平台话题标签：各平台可重写"""
        return []

    def get_style_rules(self) -> dict:
        """获取平台排版规则说明：各平台可重写"""
        return {}

    def adapt(self, title: str, content: str) -> dict:
        """统一适配入口，返回适配结果"""
        adapted_title = self.adapt_title(title)
        adapted_content = self.adapt_content(content)
        tags = self.get_tags()

        return {
            'platform_type': self.platform_type,
            'platform_name': self.platform_name,
            'platform_icon': self.platform_icon,
            'adapted_title': adapted_title,
            'adapted_content': adapted_content,
            'tags': tags,
            'style_rules': self.get_style_rules(),
            'title_length': len(adapted_title),
            'content_length': len(adapted_content)
        }

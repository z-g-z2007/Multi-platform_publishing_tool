"""
平台插件接口规范 - 所有平台插件必须实现此接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PlatformInfo:
    """平台基本信息"""
    type: str                           # 平台标识（如 'xiaohongshu'）
    name: str                           # 平台中文名（如 '小红书'）
    icon: str                           # 平台图标 emoji（如 '📕'）
    color: str                          # 主题色（如 '#FF2442'）
    description: str = ''               # 平台描述
    category: str = 'social'            # 平台分类：social/video/news/blog
    max_title_length: int = 100        # 标题最大字数
    max_content_length: int = 0        # 正文最大字数（0=不限）
    supports_images: bool = True        # 是否支持图片
    supports_video: bool = False        # 是否支持视频
    supported_formats: List[str] = field(default_factory=lambda: ['text', 'image'])  # 支持的格式

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'name': self.name,
            'icon': self.icon,
            'color': self.color,
            'description': self.description,
            'category': self.category,
            'max_title_length': self.max_title_length,
            'max_content_length': self.max_content_length,
            'supports_images': self.supports_images,
            'supports_video': self.supports_video,
            'supported_formats': self.supported_formats
        }


@dataclass
class ContentBlock:
    """内容块 - 支持多种内容类型"""
    type: str                           # 'text' | 'image' | 'video' | 'quote' | 'code'
    content: str = ''                   # 文本内容或URL
    metadata: Dict = field(default_factory=dict)  # 额外元数据


@dataclass
class AdaptedContent:
    """适配后的内容"""
    platform_type: str
    platform_name: str
    platform_icon: str
    adapted_title: str
    adapted_content: str
    tags: List[str] = field(default_factory=list)
    style_rules: Dict = field(default_factory=dict)
    title_length: int = 0
    content_length: int = 0
    image_count: int = 0
    blocks: List[ContentBlock] = field(default_factory=list)  # 结构化内容块
    metadata: Dict = field(default_factory=dict)  # 平台特定元数据

    def to_dict(self) -> dict:
        return {
            'platform_type': self.platform_type,
            'platform_name': self.platform_name,
            'platform_icon': self.platform_icon,
            'adapted_title': self.adapted_title,
            'adapted_content': self.adapted_content,
            'tags': self.tags,
            'style_rules': self.style_rules,
            'title_length': self.title_length,
            'content_length': self.content_length,
            'image_count': self.image_count,
            'blocks': [{'type': b.type, 'content': b.content, 'metadata': b.metadata} for b in self.blocks],
            'metadata': self.metadata
        }


class PlatformPluginInterface(ABC):
    """
    平台插件接口 - 所有平台适配器必须继承此类

    实现指南：
    1. 设置 platform_info 属性（平台基本信息）
    2. 实现 adapt_title() 方法（标题适配）
    3. 实现 adapt_content() 方法（正文适配）
    4. 可选实现 get_tags() 方法（获取话题标签）
    5. 可选实现 validate_content() 方法（内容校验）
    """

    @property
    @abstractmethod
    def platform_info(self) -> PlatformInfo:
        """返回平台信息"""
        pass

    @abstractmethod
    def adapt_title(self, title: str) -> str:
        """
        适配标题
        :param title: 原始标题
        :return: 适配后的标题
        """
        pass

    @abstractmethod
    def adapt_content(self, content: str, images: List[Dict] = None) -> str:
        """
        适配正文内容
        :param content: 原始正文（纯文本）
        :param images: 图片列表 [{'src': 'url', 'filename': 'xxx', 'position': 0}, ...]
        :return: 适配后的正文
        """
        pass

    def get_tags(self) -> List[str]:
        """获取平台话题标签（可选实现）"""
        return []

    def get_category_tags(self) -> List[str]:
        """获取分类标签（可选实现）"""
        return []

    def validate_content(self, title: str, content: str) -> Dict[str, any]:
        """
        校验内容是否符合平台要求（可选实现）
        :return: {'valid': bool, 'errors': List[str], 'warnings': List[str]}
        """
        errors = []
        warnings = []

        info = self.platform_info
        if info.max_title_length > 0 and len(title) > info.max_title_length:
            errors.append(f'标题超过{info.max_title_length}字限制')

        if info.max_content_length > 0 and len(content) > info.max_content_length:
            warnings.append(f'正文超过{info.max_content_length}字限制，可能被截断')

        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    def preprocess(self, title: str, content: str, images: List[Dict] = None) -> tuple:
        """
        预处理原始内容（可选实现）
        :return: (处理后的标题, 处理后的正文, 处理后的图片列表)
        """
        return title, content, images

    def postprocess(self, adapted_content: str) -> str:
        """
        后处理适配后的内容（可选实现）
        :return: 处理后的内容
        """
        return adapted_content

    def adapt(self, title: str, content: str, images: List[Dict] = None) -> AdaptedContent:
        """
        统一适配入口
        :return: AdaptedContent 对象
        """
        # 预处理
        title, content, images = self.preprocess(title, content, images)

        # 适配
        adapted_title = self.adapt_title(title)
        adapted_content = self.adapt_content(content, images or [])

        # 后处理
        adapted_content = self.postprocess(adapted_content)

        # 获取标签
        tags = self.get_tags() + self.get_category_tags()

        # 校验
        validation = self.validate_content(adapted_title, adapted_content)

        info = self.platform_info

        return AdaptedContent(
            platform_type=info.type,
            platform_name=info.name,
            platform_icon=info.icon,
            adapted_title=adapted_title,
            adapted_content=adapted_content,
            tags=tags,
            style_rules=self.get_style_rules(),
            title_length=len(adapted_title),
            content_length=len(adapted_content),
            image_count=len(images) if images else 0,
            metadata={
                'validation': validation,
                'color': info.color,
                'category': info.category
            }
        )

    def get_style_rules(self) -> Dict:
        """获取平台排版规则（可选实现）"""
        return {}

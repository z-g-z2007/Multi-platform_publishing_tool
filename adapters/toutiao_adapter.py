"""
头条号适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class ToutiaoAdapter(PlatformPluginInterface):
    """头条号平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='toutiao',
            name='头条号',
            icon='📰',
            color='#D83B34',
            description='资讯平台，热点新闻、深度报道',
            category='news',
            max_title_length=30,
            max_content_length=50000,
            supports_images=True,
            supports_video=True,
            supported_formats=['text', 'image', 'video']
        )

    def adapt_title(self, title: str) -> str:
        title = title.strip()
        # 头条标题要有吸引力
        if len(title) > 30:
            return title[:29] + '…'
        return title

    def adapt_content(self, content: str, images: List[Dict] = None) -> str:
        content = content.strip()
        images = images or []

        paragraphs = content.split('\n\n')
        adapted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            lines = para.split('\n')
            adapted_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 头条正文规范排版
                if len(line) > 60:
                    # 长句拆分
                    for i in range(0, len(line), 60):
                        adapted_lines.append(line[i:i+60])
                else:
                    adapted_lines.append(line)

            if adapted_lines:
                adapted_paragraphs.append('\n'.join(adapted_lines))

        adapted = '\n\n'.join(adapted_paragraphs)

        # 添加来源说明
        adapted += '\n\n📢 本文来源：自媒体多平台分发工具'

        return adapted

    def get_tags(self) -> List[str]:
        return ['头条', '热点', '资讯']

    def get_category_tags(self) -> List[str]:
        return ['社会', '财经', '科技', '娱乐', '体育']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '30字以内',
            'content_limit': '5万字',
            'paragraph_spacing': '段间空一行',
            'source_required': True
        }

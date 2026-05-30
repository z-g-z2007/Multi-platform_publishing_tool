"""
豆瓣适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class DoubanAdapter(PlatformPluginInterface):
    """豆瓣平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='douban',
            name='豆瓣',
            icon='🎬',
            color='#4CAF50',
            description='文化社区，书影音评、兴趣小组',
            category='social',
            max_title_length=50,
            max_content_length=5000,
            supports_images=True,
            supports_video=False,
            supported_formats=['text', 'image']
        )

    def adapt_title(self, title: str) -> str:
        title = title.strip()
        if len(title) > 50:
            return title[:49] + '…'
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

            # 豆瓣风格：文艺、有深度
            lines = para.split('\n')
            adapted_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if len(line) > 100:
                    # 长段拆分为多个短句
                    for i in range(0, len(line), 100):
                        adapted_lines.append(line[i:i+100])
                else:
                    adapted_lines.append(line)

            if adapted_lines:
                adapted_paragraphs.append('\n'.join(adapted_lines))

        adapted = '\n\n'.join(adapted_paragraphs)

        return adapted

    def get_tags(self) -> List[str]:
        return ['豆瓣', '文艺', '兴趣']

    def get_category_tags(self) -> List[str]:
        return ['电影', '读书', '音乐', '旅行', '摄影']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '50字以内',
            'content_limit': '5000字',
            'style': '文艺腔、有深度思考'
        }

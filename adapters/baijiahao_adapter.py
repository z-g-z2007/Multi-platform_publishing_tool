"""
百家号适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class BaijiahaoAdapter(PlatformPluginInterface):
    """百家号平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='baijiahao',
            name='百家号',
            icon='🏆',
            color='#3266FF',
            description='百度内容平台，SEO优化、搜索流量',
            category='blog',
            max_title_length=30,
            max_content_length=50000,
            supports_images=True,
            supports_video=True,
            supported_formats=['text', 'image', 'video']
        )

    def adapt_title(self, title: str) -> str:
        title = title.strip()
        # 百家号标题SEO友好
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
                # 百家号规范排版
                if len(line) > 50:
                    for i in range(0, len(line), 50):
                        adapted_lines.append(line[i:i+50])
                else:
                    adapted_lines.append(line)

            if adapted_lines:
                adapted_paragraphs.append('\n'.join(adapted_lines))

        adapted = '\n\n'.join(adapted_paragraphs)

        return adapted

    def get_tags(self) -> List[str]:
        return ['百家号', '百度', '原创']

    def get_category_tags(self) -> List[str]:
        return ['互联网', '科技', '数码', '评测']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '30字以内',
            'content_limit': '5万字',
            'seo_optimized': True,
            'original_tag': '必须标注原创'
        }

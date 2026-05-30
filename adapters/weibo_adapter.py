"""
微博适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class WeiboAdapter(PlatformPluginInterface):
    """微博平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='weibo',
            name='微博',
            icon='📣',
            color='#E6162D',
            description='社交媒体平台，热点资讯、粉丝互动',
            category='social',
            max_title_length=50,
            max_content_length=2000,
            supports_images=True,
            supports_video=True,
            supported_formats=['text', 'image', 'video']
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

            # 微博短句风格
            lines = para.split('\n')
            adapted_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 每行不超过50字
                if len(line) > 50:
                    adapted_lines.append(line[:49] + '…')
                else:
                    adapted_lines.append(line)

            if adapted_lines:
                adapted_paragraphs.append(' '.join(adapted_lines))

        adapted = '\n'.join(adapted_paragraphs)

        # 添加图片标记
        if images:
            img_count = min(len(images), 9)
            adapted += '\n\n'
            for i in range(img_count):
                adapted += f'[#图片#{i+1}]\n'

        return adapted

    def get_tags(self) -> List[str]:
        return ['微博', '超话', '粉丝']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '50字以内',
            'content_limit': '2000字',
            'image_limit': '9张',
            'line_break': '用换行分隔不同短句'
        }

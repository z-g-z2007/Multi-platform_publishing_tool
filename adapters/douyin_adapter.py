"""
抖音适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class DouyinAdapter(PlatformPluginInterface):
    """抖音平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='douyin',
            name='抖音',
            icon='🎵',
            color='#FE2C55',
            description='短视频平台，创意内容、热门挑战',
            category='video',
            max_title_length=30,
            max_content_length=2000,
            supports_images=False,
            supports_video=True,
            supported_formats=['text', 'video']
        )

    def adapt_title(self, title: str) -> str:
        title = title.strip()
        if len(title) > 30:
            return title[:29] + '…'
        return title

    def adapt_content(self, content: str, images: List[Dict] = None) -> str:
        content = content.strip()

        # 抖音：短小精悍，吸引眼球
        paragraphs = content.split('\n\n')
        adapted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            lines = para.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 每句话单独成行，保持节奏感
                if len(line) > 40:
                    adapted_paragraphs.append(line[:39] + '…')
                else:
                    adapted_paragraphs.append(line)

        adapted = '\n'.join(adapted_paragraphs)

        # 添加话题标记
        adapted += '\n\n#抖音 #热门 #推荐'

        return adapted

    def get_tags(self) -> List[str]:
        return ['抖音', '短视频', '热门']

    def get_category_tags(self) -> List[str]:
        return ['搞笑', '情感', '生活', '音乐']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '30字以内',
            'content_limit': '2000字',
            'video_required': True,
            'hashtags': '3-5个热门话题'
        }

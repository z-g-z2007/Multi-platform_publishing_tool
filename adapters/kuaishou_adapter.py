"""
快手适配器 - 扩展示例插件
"""
from typing import List, Dict

from .plugin_interface import PlatformPluginInterface, PlatformInfo


class KuaishouAdapter(PlatformPluginInterface):
    """快手平台适配器"""

    @property
    def platform_info(self) -> PlatformInfo:
        return PlatformInfo(
            type='kuaishou',
            name='快手',
            icon='📱',
            color='#FF4906',
            description='短视频平台，老铁文化、真实生活',
            category='video',
            max_title_length=25,
            max_content_length=1000,
            supports_images=False,
            supports_video=True,
            supported_formats=['text', 'video']
        )

    def adapt_title(self, title: str) -> str:
        title = title.strip()
        if len(title) > 25:
            return title[:24] + '…'
        return title

    def adapt_content(self, content: str, images: List[Dict] = None) -> str:
        content = content.strip()

        # 快手：接地气，真性情
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
                # 快手风格：口语化
                if len(line) > 35:
                    adapted_paragraphs.append(line[:34] + '…')
                else:
                    adapted_paragraphs.append(line)

        adapted = '\n'.join(adapted_paragraphs)

        # 添加标签
        adapted += '\n\n#快手 #老铁 #双击'

        return adapted

    def get_tags(self) -> List[str]:
        return ['快手', '短视频', '老铁']

    def get_style_rules(self) -> Dict:
        return {
            'title_limit': '25字以内',
            'content_limit': '1000字',
            'style': '接地气、口语化'
        }

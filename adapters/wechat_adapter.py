"""
微信公众号适配器 - 正式长文风格
适配规则：
1. 保留标准正式排版，段落间距规整
2. 支持标题层级格式化（##、###）
3. 正文首行缩进（两个全角空格）
4. 去除多余花哨符号，适配公众号正式文风
5. 适配长图文、长文章格式，无字数截断
6. 段落间保持统一间距，排版工整
"""
import re
from .base_adapter import BaseAdapter


class WechatAdapter(BaseAdapter):
    platform_name = '微信公众号'
    platform_type = 'wechat'
    platform_icon = '💬'
    title_max_length = 64
    platform_description = '正式长文风格，排版工整，适合深度阅读'

    def adapt_title(self, title: str) -> str:
        """公众号标题：64字以内"""
        title = title.strip()
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str) -> str:
        """公众号正文适配：标准化排版，正式文风"""
        content = content.strip()

        # 1. 识别并格式化标题层级
        content = self._format_headings(content)

        # 2. 清理多余符号
        content = self._clean_excessive_symbols(content)

        # 3. 规范段落间距（最多保留一个空行）
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 4. 段落首行缩进
        paragraphs = content.split('\n')
        formatted = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                formatted.append('')
                continue

            # 标题行不加缩进
            if para.startswith(('##', '###', '【', '「', '《', '一、', '二、', '三、',
                               '四、', '五、', '六、', '七、', '八、', '九、', '十、',
                               '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                formatted.append(para)
            else:
                formatted.append(f'　　{para}')  # 全角空格缩进

        adapted = '\n'.join(formatted)

        # 5. 添加公众号标准结尾
        footer = '\n\n---\n\n*本文由自媒体多平台分发工具自动排版*\n*关注我们，获取更多精彩内容*'
        adapted = f'{adapted}{footer}'

        return adapted

    def _format_headings(self, content: str) -> str:
        """智能识别标题并添加层级标记"""
        lines = content.split('\n')
        formatted_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue

            # 如果已经是标题格式，保留
            if stripped.startswith(('#', '##', '###')):
                formatted_lines.append(stripped)
                continue

            # 检测可能是标题的行（短行、在段落之间）
            is_potential_heading = False
            # 条件1：长度在5-30字之间
            if 5 <= len(stripped) <= 30:
                # 条件2：不包含句末标点
                if not re.search(r'[。！？；，、.!?;,]', stripped):
                    # 条件3：前后有空行（或者是第一行/最后一行）
                    prev_empty = i == 0 or not lines[i - 1].strip()
                    next_empty = i == len(lines) - 1 or not lines[i + 1].strip()
                    if prev_empty and next_empty:
                        is_potential_heading = True

            if is_potential_heading:
                formatted_lines.append(f'## {stripped}')
            else:
                formatted_lines.append(stripped)

        return '\n'.join(formatted_lines)

    def _clean_excessive_symbols(self, content: str) -> str:
        """清理多余符号，适配正式文风"""
        # 重复标点符号归一化
        content = re.sub(r'[!！]{2,}', '！', content)
        content = re.sub(r'[?？]{2,}', '？', content)
        content = re.sub(r'[.。]{2,}', '。', content)
        content = re.sub(r'[~～]{2,}', '', content)  # 去除波浪线

        # 去除过度的Emoji表情（保留个别常用表情）
        excessive_emoji = r'[😜😝😛🤪🤩🥳🤯😈👿💀☠️👻👽🤖👾]'
        content = re.sub(excessive_emoji, '', content)

        # 去除连续空格
        content = re.sub(r' {2,}', ' ', content)

        # 去除行末多余空格
        content = re.sub(r' +\n', '\n', content)

        return content

    def get_style_rules(self) -> dict:
        return {
            '标题字数': '≤64字',
            '段落规则': '首行全角空格缩进，段落间空行分隔',
            '排版风格': '正式标准化排版，智能识别标题层级',
            '符号清理': '去除多余标点、过度Emoji、波浪线',
            '字数限制': '无字数截断，支持长文',
            '适用场景': '公众号推文、深度长文、品牌宣传'
        }

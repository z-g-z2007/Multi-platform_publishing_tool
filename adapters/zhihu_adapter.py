"""
知乎适配器 - 干货正式文风
适配规则：
1. 偏向干货、正式文风，自动精简冗余口语化文字
2. 规整段落逻辑，适合问答、专栏内容展示
3. 去除多余表情、无效符号，保持内容严谨
4. 合并过短段落，增强逻辑连贯性
5. 智能添加引用块和列表格式
"""
import re
from .base_adapter import BaseAdapter


class ZhihuAdapter(BaseAdapter):
    platform_name = '知乎'
    platform_type = 'zhihu'
    platform_icon = '💡'
    title_max_length = 100
    platform_description = '干货正式文风，内容严谨，适合知识分享'

    def adapt_title(self, title: str) -> str:
        """知乎标题：100字以内，优化为提问式或陈述式"""
        title = title.strip()
        # 如果标题过短，尝试优化为更有吸引力的知乎体
        if len(title) < 10 and '?' not in title and '？' not in title:
            title = f'{title}，究竟有什么门道？'
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str) -> str:
        """知乎正文适配：干货风，去口语化，逻辑清晰"""
        content = content.strip()

        # 1. 清理Emoji表情（知乎偏严肃风格）
        content = self._remove_emojis(content)

        # 2. 去除口语化表达
        content = self._remove_informal_expressions(content)

        # 3. 规范化标点符号
        content = self._normalize_punctuation(content)

        # 4. 合并过短段落，增强逻辑连贯
        content = self._merge_short_paragraphs(content)

        # 5. 智能格式化（引用块、列表）
        content = self._smart_format(content)

        # 6. 添加知乎标准结尾
        footer = '\n\n> 以上为个人观点，欢迎在评论区交流讨论。\n\n*觉得有用的话，不妨点个赞同支持一下~*'
        content = f'{content}{footer}'

        return content

    def _remove_emojis(self, content: str) -> str:
        """移除所有Emoji表情"""
        emoji_pattern = re.compile(
            '[\U0001F600-\U0001F64F'  # 表情符号
            '\U0001F300-\U0001F5FF'   # 符号和象形文字
            '\U0001F680-\U0001F6FF'   # 交通和地图符号
            '\U0001F1E0-\U0001F1FF'   # 旗帜
            '\U00002702-\U000027B0'   # 其他符号
            '\U000024C2-\U0001F251'   # 其他
            '\U0001F900-\U0001F9FF'   # 补充符号和象形文字
            '\U0001FA00-\U0001FA6F'   # 象棋符号
            '\U0001FA70-\U0001FAFF'   # 扩展A
            '\U00002600-\U000026FF'   # 杂项符号
            '\U0000FE00-\U0000FE0F'   # 变体选择器
            ']+', flags=re.UNICODE)
        return emoji_pattern.sub('', content)

    def _remove_informal_expressions(self, content: str) -> str:
        """去除口语化表达"""
        # 去除句末语气词
        content = re.sub(r'[嗯啊呀呢啦吧哦哈呵嘿哟嘛]{1,}[~～]*', '', content)
        content = re.sub(r'嘻嘻|哈哈|呵呵|嘿嘿|吼吼|呜呜|哇塞|天呐|哎呀|哎哟', '', content)

        # 替换口语化短语
        informal_replacements = {
            r'那个': '',
            r'然后呢': '然后',
            r'就是说': '也就是说',
            r'其实吧': '其实',
            r'怎么说呢': '',
            r'讲真的': '客观来说',
            r'说白了': '简而言之',
            r'不得不说': '',
            r'你知道吗': '',
            r'你想啊': '',
            r'我跟你说': '',
        }
        for pattern, replacement in informal_replacements.items():
            content = re.sub(pattern, replacement, content)

        # 清理多余空格和空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)

        return content

    def _normalize_punctuation(self, content: str) -> str:
        """规范化标点符号"""
        # 重复标点归一化
        content = re.sub(r'[!！]{2,}', '！', content)
        content = re.sub(r'[?？]{2,}', '？', content)
        content = re.sub(r'[.。]{3,}', '……', content)
        content = re.sub(r'[,，]{2,}', '，', content)

        # 半角标点转全角（中文环境）
        punct_map = {
            ',': '，', '.': '。', '!': '！', '?': '？',
            ';': '；', ':': '：', '(': '（', ')': '）',
        }
        # 只在中文语境下转换
        for en_punct, cn_punct in punct_map.items():
            content = re.sub(
                rf'([\u4e00-\u9fff]){re.escape(en_punct)}([\u4e00-\u9fff])',
                rf'\1{cn_punct}\2',
                content
            )

        return content

    def _merge_short_paragraphs(self, content: str) -> str:
        """合并过短段落，增强逻辑连贯性"""
        paragraphs = content.split('\n')
        merged = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                if merged and merged[-1] != '':
                    merged.append('')
                continue

            # 过短的段落（<15字）合并到上一段
            if len(para) < 15 and merged and merged[-1] != '' and not merged[-1].startswith(('>', '-', '1.')):
                merged[-1] = merged[-1] + para
            else:
                merged.append(para)

        return '\n\n'.join(p for p in merged if p or (merged and merged[-1] != ''))

    def _smart_format(self, content: str) -> str:
        """智能格式化：识别列表、引用等"""
        lines = content.split('\n')
        formatted = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted.append('')
                continue

            # 检测数字列表（如"1、xxx"或"1.xxx"）
            list_match = re.match(r'^(\d+)[、.]\s*(.+)', stripped)
            if list_match:
                formatted.append(f'{list_match.group(1)}. {list_match.group(2)}')
                continue

            # 检测破折号列表
            if stripped.startswith(('-', '•', '·', '◆', '◇', '○', '●')):
                formatted.append(f'- {stripped.lstrip("-•·◆◇○● ")}')
                continue

            formatted.append(stripped)

        return '\n'.join(formatted)

    def get_style_rules(self) -> dict:
        return {
            '标题字数': '≤100字，智能优化为知乎体',
            '段落规则': '短段合并，增强逻辑连贯性',
            '排版风格': '严谨正式，去除Emoji和口语化',
            '标点规范': '中英文标点统一，去除重复标点',
            '特殊格式': '自动识别列表项和引用块',
            '适用场景': '问答、专栏文章、知识分享、深度讨论'
        }

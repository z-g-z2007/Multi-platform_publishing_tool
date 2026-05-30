"""
知乎适配器 - 专业/干货风格（问答/专栏）
适配规则：
1. 标题：问答式/结论式，如"如何高效学习？""这3个方法，让你效率翻倍"
2. 正文：Markdown格式，专业严谨，信息密度高
3. 结构：直接回答/结论先行开头 → 层级标题+分点+加粗重点+引用主体 → 总结+互动结尾
4. 关键词：自然融入，专业术语准确
"""
import re
from .base_adapter import BaseAdapter


class ZhihuAdapter(BaseAdapter):
    platform_name = '知乎'
    platform_type = 'zhihu'
    platform_icon = '💡'
    title_max_length = 30
    content_max_length = 5000
    platform_description = '干货正式文风，内容严谨，适合知识分享'

    def adapt_title(self, title: str) -> str:
        """知乎标题：问答式/结论式，突出干货/价值"""
        title = title.strip()
        
        # 如果不是问句形式，尝试转换为问答或结论式
        if '？' not in title and '？' not in title:
            # 检查是否包含数字
            if any(c.isdigit() for c in title):
                # 结论式标题
                title = f'{title}，亲测有效'
            else:
                # 问答式标题
                title = f'如何{title}？'
        
        # 截断到30字
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        
        return title

    def adapt_content(self, content: str, images: list = None) -> str:
        """知乎正文：Markdown格式，专业严谨，信息密度高，支持图文混排"""
        content = content.strip()
        images = images or []

        # 1. 分段处理
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # 2. 处理成Markdown格式
        processed_lines = []
        list_mode = False
        list_number = 1
        img_index = 0
        
        for i, para in enumerate(paragraphs):
            # 检测列表项
            if para.startswith(('1.', '2.', '3.', '-', '*', '·', '、')):
                if not list_mode:
                    processed_lines.append('')  # 添加空行
                    list_mode = True
                # 标准化列表格式
                if para[0].isdigit():
                    processed_lines.append(f'{list_number}. {para[2:].strip()}')
                    list_number += 1
                else:
                    processed_lines.append(f'- {para[1:].strip()}')
            else:
                if list_mode:
                    processed_lines.append('')  # 添加空行结束列表
                    list_mode = False
                    list_number = 1
                
                if i == 0:
                    # 开头：结论先行
                    processed_lines.append(f'**结论先行**：{para}')
                elif len(para) > 150:
                    # 长段落：添加二级标题
                    section_title = self._extract_section_title(para)
                    processed_lines.append(f'## {section_title}')
                    processed_lines.append(para)
                    # 在重要章节后插入图片
                    if img_index < len(images):
                        processed_lines.append(f'![图{img_index + 1}](image_{img_index + 1}.png)')
                        img_index += 1
                elif len(para) > 80:
                    # 中等段落：加粗开头关键词
                    keywords = ['首先', '其次', '然后', '最后', '总之', '因此', '然而', '值得注意的是']
                    for kw in keywords:
                        if para.startswith(kw):
                            para = f'**{kw}**{para[len(kw):]}'
                            break
                    processed_lines.append(para)
                else:
                    processed_lines.append(para)

        # 3. 添加引用块
        adapted = '\n\n'.join(processed_lines)
        adapted = self._add_blockquotes(adapted)

        # 4. 添加重点加粗
        adapted = self._add_emphasis(adapted)

        # 5. 结尾互动引导
        interaction_guide = '''

---

**总结一下：**
以上是我的分享，如果对你有帮助，欢迎点赞、收藏、关注～
有任何问题或补充，欢迎在评论区交流！
        '''

        # 6. 组合最终内容
        result = f'{adapted}{interaction_guide}'
        
        # 7. 控制总字数
        if len(result) > self.content_max_length:
            result = result[:self.content_max_length - 100] + '…\n\n---\n\n（全文较长，核心观点已呈现）'

        return result

    def _extract_section_title(self, text: str) -> str:
        """从文本中提取小标题"""
        title = text[:30].strip()
        title = re.sub(r'[。！？；,，]$', '', title)
        # 添加序号
        return title

    def _add_blockquotes(self, text: str) -> str:
        """为引用内容添加Markdown引用块"""
        # 识别并处理引用内容
        lines = text.split('\n')
        result = []
        in_quote = False
        
        for line in lines:
            # 简单识别引用（以"引用"、"参考"、"资料"开头）
            if line.strip().startswith(('引用', '参考', '资料来源', '注：')):
                result.append(f'> {line.strip()}')
                in_quote = True
            elif in_quote and line.strip():
                result.append(f'> {line.strip()}')
            else:
                result.append(line)
                in_quote = False
        
        return '\n'.join(result)

    def _add_emphasis(self, text: str) -> str:
        """添加重点标记（加粗）"""
        # 对专业术语和关键词进行加粗处理
        keywords = ['重要', '核心', '关键', '注意', '必须', '建议', '推荐', 
                   '技巧', '方法', '结论', '分析', '数据', '研究', '表明']
        for kw in keywords:
            text = text.replace(kw, f'**{kw}**')
        return text

    def get_tags(self) -> list:
        return ['#知识分享', '#干货', '#经验分享', '#学习', '#职场']

    def get_style_rules(self) -> dict:
        return {
            '标题规则': '问答式/结论式，突出干货/价值',
            '格式规范': 'Markdown格式，支持层级标题、列表、加粗、引用',
            '结构要求': '结论先行开头(1-2段) → 层级标题+分点+加粗重点+引用主体 → 总结+互动结尾',
            '字体规范': '默认字体，加粗/斜体/引用区分层级',
            '关键词要求': '自然融入，专业术语准确，引用标注来源',
            '字数限制': '问答500-3000字，专栏1000-5000字',
            '适用场景': '知识分享、专业问答、学术讨论、行业分析'
        }

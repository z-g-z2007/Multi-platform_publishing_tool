"""
微信公众号适配器 - 长文/富文本风格（深度阅读）
适配规则：
1. 标题15-20字：痛点/悬念/数字+关键词
2. 正文1000-5000字：富文本格式，规范排版
3. 结构：摘要(≤54字) → 场景引入+核心观点开头 → 小标题+分段阐述+配图主体 → 总结+互动引导结尾
4. 格式：中文与英文/数字间加半角空格，重点加粗/变色
"""
import re
from .base_adapter import BaseAdapter


class WechatAdapter(BaseAdapter):
    platform_name = '微信公众号'
    platform_type = 'wechat'
    platform_icon = '💬'
    title_max_length = 20
    content_max_length = 5000
    platform_description = '正式长文风格，排版工整，适合深度阅读'

    def adapt_title(self, title: str) -> str:
        """公众号标题：15-20字，痛点/悬念/数字+关键词"""
        title = title.strip()
        
        # 如果标题太短，尝试添加悬念元素
        if len(title) < 10:
            title = f'关于{title}，你需要知道的事'
        
        # 截断到20字
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        
        return title

    def adapt_content(self, content: str, images: list = None) -> str:
        """公众号正文：富文本格式，规范排版，支持图文混排"""
        content = content.strip()
        images = images or []

        # 1. 提取或生成摘要（≤54字）
        summary = self._extract_summary(content)
        
        # 2. 分段处理，确保段落清晰
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # 3. 为长段落添加小标题
        processed_paragraphs = []
        section_count = 1
        img_index = 0
        
        for i, para in enumerate(paragraphs):
            # 如果段落过长（>200字），拆分成多个段落
            if len(para) > 200:
                chunks = self._split_long_paragraph(para)
                for j, chunk in enumerate(chunks):
                    if j == 0 and i > 0:
                        # 为新段落添加小标题
                        processed_paragraphs.append(f'▌第{section_count}部分：{self._extract_section_title(chunk)}')
                        section_count += 1
                    processed_paragraphs.append(chunk)
                    # 在适当位置插入图片标记
                    if img_index < len(images) and (j + 1) % 2 == 0:
                        processed_paragraphs.append(f'🖼️ 图{img_index + 1}：相关配图')
                        img_index += 1
            else:
                if i == 0:
                    processed_paragraphs.append(para)
                elif len(para) > 100:
                    # 为重要段落添加小标题
                    processed_paragraphs.append(f'▌{self._extract_section_title(para)}')
                    processed_paragraphs.append(para)
                else:
                    processed_paragraphs.append(para)
            
            # 在长内容中适当插入图片
            if img_index < len(images) and i > 0 and i % 3 == 0:
                processed_paragraphs.append(f'🖼️ 图{img_index + 1}：相关配图')
                img_index += 1

        # 4. 中文与英文/数字间加半角空格
        adapted = '\n\n'.join([self._add_spaces(p) for p in processed_paragraphs])

        # 5. 添加重点标记（加粗）
        adapted = self._add_emphasis(adapted)

        # 6. 结尾互动引导
        interaction_guide = '''

---

💡 **今日互动**
欢迎在评论区分享你的看法～
如果觉得文章对你有帮助，记得点赞、在看、转发三连支持！

📮 关注【公众号名称】，获取更多优质内容
        '''

        # 7. 组合最终内容
        result = f'【摘要】{summary}\n\n{adapted}{interaction_guide}'
        
        # 8. 控制总字数
        if len(result) > self.content_max_length:
            result = result[:self.content_max_length - 100] + '…\n\n---\n\n全文阅读请点击【阅读原文】'

        return result

    def _extract_summary(self, content: str) -> str:
        """提取或生成摘要（≤54字）"""
        content = content.strip()
        # 取前54字作为摘要
        summary = content[:54]
        # 如果在句子中间截断，找到最近的标点
        if len(content) > 54:
            for punct in ['。', '！', '？', '；', '.', '!', '?']:
                pos = summary.rfind(punct)
                if pos > 0:
                    summary = summary[:pos + 1]
                    break
        return summary

    def _split_long_paragraph(self, para: str, max_len: int = 200) -> list:
        """拆分长段落"""
        chunks = []
        while len(para) > max_len:
            # 优先在标点处断开
            split_pos = max_len
            for punct in ['。', '！', '？', '；', '\n']:
                pos = para[:max_len].rfind(punct)
                if pos > max_len // 2:
                    split_pos = pos + 1
                    break
            chunks.append(para[:split_pos])
            para = para[split_pos:]
        if para:
            chunks.append(para)
        return chunks

    def _extract_section_title(self, text: str) -> str:
        """从文本中提取小标题"""
        # 取前20字作为小标题
        title = text[:20].strip()
        # 去掉末尾标点
        title = re.sub(r'[。！？；,，]$', '', title)
        return title

    def _add_spaces(self, text: str) -> str:
        """中文与英文/数字间加半角空格"""
        # 中文后跟英文/数字
        text = re.sub(r'([\u4e00-\u9fa5])([a-zA-Z0-9])', r'\1 \2', text)
        # 英文/数字后跟中文
        text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fa5])', r'\1 \2', text)
        return text

    def _add_emphasis(self, text: str) -> str:
        """添加重点标记（加粗）"""
        # 对关键词进行加粗处理
        keywords = ['重要', '核心', '关键', '注意', '必须', '建议', '推荐', '技巧', '方法']
        for kw in keywords:
            text = text.replace(kw, f'**{kw}**')
        return text

    def get_tags(self) -> list:
        return []

    def get_style_rules(self) -> dict:
        return {
            '标题规则': '15-20字，痛点/悬念/数字+关键词',
            '摘要要求': '≤54字，提炼核心内容',
            '字体规范': '标题20-24px加粗，正文15-16px，注释12-14px浅灰',
            '间距规范': '行间距1.5-1.8倍，段落间距比行高大5-8px，首行缩进2字符',
            '格式规范': '中文与英文/数字间加半角空格，重点加粗/变色',
            '结构要求': '摘要 → 场景引入+核心观点开头 → 小标题+分段阐述+配图 → 总结+互动引导',
            '字数限制': '正文1000-5000字',
            '适用场景': '深度长文、知识分享、行业分析、观点表达'
        }

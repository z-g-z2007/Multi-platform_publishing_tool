"""
小红书适配器 - 图文笔记风格（种草/笔记风）
适配规则：
1. 标题≤20字：关键词 + 结果/情绪 + emoji
2. 正文≤1000字：每段1-3行，短句为主，段间空一行
3. 结构：痛点+结论开头 → emoji+短句+分点主体 → 引导互动结尾
4. 标签：#关键词 #细分领域 #热门标签
"""
import re
from .base_adapter import BaseAdapter


class XiaohongshuAdapter(BaseAdapter):
    platform_name = '小红书'
    platform_type = 'xiaohongshu'
    platform_icon = '📕'
    platform_icon_url = '/static/platforms/xiaohongshu.jpeg'
    title_max_length = 20
    content_max_length = 1000
    platform_color = '#FF2442'
    platform_description = '图文笔记风格，种草/笔记风，适合手机阅读'

    # 多领域话题标签库
    TOPIC_LIBRARY = {
        '美食': ['#美食探店', '#美食分享', '#今天吃什么', '#美食日常', '#吃货日记'],
        '穿搭': ['#今日穿搭', '#OOTD', '#穿搭灵感', '#时尚穿搭', '#每日穿搭'],
        '美妆': ['#美妆分享', '#好物推荐', '#护肤心得', '#彩妆教程', '#变美日记'],
        '旅行': ['#旅行攻略', '#小众打卡地', '#周末去哪儿', '#旅行日记', '#城市漫游'],
        '学习': ['#学习打卡', '#自我提升', '#效率工具', '#知识分享', '#读书笔记'],
        '数码': ['#数码好物', '#科技生活', '#效率App', '#生产力工具', '#数码测评'],
        '职场': ['#职场心得', '#工作日常', '#效率提升', '#职场穿搭', '#办公好物'],
        '通用': ['#干货分享', '#实用技巧', '#经验分享', '#宝藏推荐', '#冷知识']
    }

    def _detect_topic_category(self, content: str) -> str:
        """根据内容关键词智能匹配话题类别"""
        keywords_map = {
            '美食': ['美食', '好吃', '餐厅', '外卖', '做饭', '菜谱', '食材', '甜品', '奶茶', '咖啡'],
            '穿搭': ['穿搭', '衣服', '裙子', '裤子', '外套', '鞋', '包', '配饰', '搭配'],
            '美妆': ['护肤', '化妆', '口红', '粉底', '面膜', '精华', '防晒', '香水'],
            '旅行': ['旅行', '旅游', '景点', '打卡', '攻略', '酒店', '民宿', '出行'],
            '学习': ['学习', '读书', '课程', '笔记', '考试', '技能', '提升', '知识'],
            '数码': ['手机', '电脑', 'app', '软件', '数码', '科技', '智能', '耳机'],
            '职场': ['工作', '职场', '办公', '效率', '同事', '加班', '升职', '面试'],
        }
        for category, keywords in keywords_map.items():
            for kw in keywords:
                if kw in content:
                    return category
        return '通用'

    def adapt_title(self, title: str) -> str:
        """小红书标题：≤20字，关键词+结果/情绪+emoji"""
        title = title.strip()
        
        # 智能添加Emoji前缀（根据关键词）
        emoji_prefix_map = {
            '美食': '🍽️', '好吃': '😋', '餐厅': '🍴', '做饭': '👩‍🍳', '甜品': '🍰',
            '穿搭': '👗', '衣服': '✨', '美妆': '💄', '护肤': '🧴',
            '旅行': '✈️', '打卡': '📍', '攻略': '📝',
            '学习': '📚', '读书': '📖', '技能': '💡',
            '数码': '📱', '推荐': '🌟', '分享': '💬', '干货': '🔥',
            '减脂': '✅', '减肥': '💪', '瘦': '🏃',
            '急救': '🚑', '熬夜': '🌙', '脸黄': '😰',
        }
        emoji_added = False
        for keyword, emoji in emoji_prefix_map.items():
            if keyword in title:
                title = f'{emoji}{title}'
                emoji_added = True
                break
        if not emoji_added:
            title = f'✨{title}'

        # 截断到20字
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str, images: list = None) -> str:
        """小红书正文：≤1000字，每段1-3行，短句为主，段间空一行，支持图文混排"""
        content = content.strip()
        images = images or []

        # 1. 按段落分割，过滤空行
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        # 2. 每段不超过3行，每行不超过30字
        short_paragraphs = []
        for para in paragraphs:
            lines = []
            current_line = ''
            for char in para:
                current_line += char
                if len(current_line) >= 30 or char in ['。', '！', '？', '；']:
                    lines.append(current_line)
                    current_line = ''
            if current_line:
                lines.append(current_line)
            
            # 每段最多3行
            short_paragraphs.extend(lines[:3])

        # 3. 段间空一行
        adapted = '\n\n'.join(short_paragraphs)

        # 4. 添加emoji分段标记
        separator_emojis = ['🍃', '✨', '💡', '🌟', '📌', '🔍', '💫', '🎯', '🔥']
        lines = adapted.split('\n\n')
        decorated_lines = []
        for i, line in enumerate(lines):
            if i > 0 and len(line) > 5:
                emoji = separator_emojis[i % len(separator_emojis)]
                decorated_lines.append(f'{emoji} {line}')
            else:
                decorated_lines.append(line)
        adapted = '\n\n'.join(decorated_lines)

        # 5. 添加图片标记（小红书图文笔记风格）
        if images:
            img_markers = '\n\n'.join([f'🖼️ 配图{i+1}' for i in range(min(len(images), 9))])
            adapted = f'{adapted}\n\n{img_markers}'

        # 6. 智能话题标签（根据内容匹配）
        category = self._detect_topic_category(content)
        topics = self.TOPIC_LIBRARY.get(category, self.TOPIC_LIBRARY['通用'])
        topic_str = ' '.join(topics[:6])

        # 7. 结尾引导互动
        interaction_prompts = [
            '💬 你们觉得怎么样？评论区聊聊吧～',
            '❤️ 喜欢的话记得点赞收藏哦！',
            '👇 有什么问题欢迎评论区交流～',
            '🌟 关注我，获取更多实用干货！',
            '📮 私信我了解更多详情～',
        ]
        prompt = interaction_prompts[hash(content) % len(interaction_prompts)]

        # 8. 控制总字数≤1000
        result = f'{adapted}\n\n{topic_str}\n\n{prompt}'
        if len(result) > self.content_max_length:
            result = result[:self.content_max_length - 30] + '…\n\n' + topic_str
        
        return result

    def get_tags(self) -> list:
        return list(self.TOPIC_LIBRARY['通用'])

    def get_style_rules(self) -> dict:
        return {
            '标题规则': '≤20字，关键词+结果/情绪+emoji',
            '段落规则': '每段1-3行，短句为主，段间空一行',
            '结构要求': '痛点+结论开头 → emoji+短句+分点主体 → 引导互动结尾',
            '字体颜色': '默认字体，颜色≤3种（黑/深灰+1种强调色）',
            '话题标签': '根据内容智能匹配6个热门话题',
            '字数限制': '正文≤1000字',
            '适用场景': '图文笔记、种草推荐、生活分享'
        }

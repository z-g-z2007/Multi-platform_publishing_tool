"""
小红书适配器 - 图文笔记风格
适配规则：
1. 标题控制在20字以内，适合手机端展示
2. 段落简短分段，每段不超过50字，自动换行
3. 自动添加5-8个热门话题标签，覆盖多领域
4. 添加Emoji装饰增强视觉吸引力
5. 过滤超长段落，优化轻量化文案排版
6. 末尾添加互动引导语
"""
import re
from .base_adapter import BaseAdapter


class XiaohongshuAdapter(BaseAdapter):
    platform_name = '小红书'
    platform_type = 'xiaohongshu'
    platform_icon = '📕'
    title_max_length = 20
    platform_description = '图文笔记风格，短平快，适合手机阅读'

    # 多领域话题标签库
    TOPIC_LIBRARY = {
        '生活': ['#日常分享', '#生活碎片', '#我的日常', '#记录生活', '#生活美学'],
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
        """小红书标题：20字以内，自动添加Emoji前缀"""
        title = title.strip()
        # 智能添加Emoji前缀
        emoji_prefix_map = {
            '美食': '🍽️', '好吃': '😋', '餐厅': '🍴', '做饭': '👩‍🍳', '甜品': '🍰',
            '穿搭': '👗', '衣服': '✨', '美妆': '💄', '护肤': '🧴',
            '旅行': '✈️', '打卡': '📍', '攻略': '📝',
            '学习': '📚', '读书': '📖', '技能': '💡',
            '数码': '📱', '推荐': '🌟', '分享': '💬', '干货': '🔥',
        }
        emoji_added = False
        for keyword, emoji in emoji_prefix_map.items():
            if keyword in title:
                title = f'{emoji} {title}'
                emoji_added = True
                break
        if not emoji_added:
            title = f'✨ {title}'

        # 截断到20字
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str) -> str:
        """小红书正文适配：短段落 + 话题标签 + 互动引导"""
        content = content.strip()

        # 1. 按段落分割
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        short_paragraphs = []

        for para in paragraphs:
            # 2. 每段不超过50字，自动拆分
            while len(para) > 50:
                # 优先在标点符号处断开
                split_pos = 50
                for punct in ['。', '！', '？', '；', '.', '!', '?', '；', '\n']:
                    pos = para[:50].rfind(punct)
                    if pos > 25:
                        split_pos = pos + 1
                        break
                short_paragraphs.append(para[:split_pos])
                para = para[split_pos:]
            short_paragraphs.append(para)

        # 3. 每个段落之间用空行分隔
        adapted = '\n\n'.join(short_paragraphs)

        # 4. 添加Emoji分段标记（让内容更活泼）
        separator_emojis = ['✨', '💡', '🌟', '📌', '🔍', '💫', '🎯', '🔥']
        lines = adapted.split('\n\n')
        decorated_lines = []
        for i, line in enumerate(lines):
            if i > 0 and len(line) > 10:
                emoji = separator_emojis[i % len(separator_emojis)]
                decorated_lines.append(f'{emoji} {line}')
            else:
                decorated_lines.append(line)
        adapted = '\n\n'.join(decorated_lines)

        # 5. 智能话题标签（根据内容匹配）
        category = self._detect_topic_category(content)
        topics = self.TOPIC_LIBRARY.get(category, self.TOPIC_LIBRARY['通用'])
        topic_str = ' '.join(topics[:6])  # 最多6个标签

        # 6. 末尾互动引导
        interaction_prompts = [
            '💬 你们觉得怎么样？评论区聊聊吧~',
            '❤️ 喜欢的话记得点赞收藏哦！',
            '👇 有什么问题欢迎评论区交流~',
            '🌟 关注我，获取更多实用干货！',
            '📮 私信我了解更多详情~',
        ]
        prompt = interaction_prompts[hash(content) % len(interaction_prompts)]

        adapted = f'{adapted}\n\n{topic_str}\n\n{prompt}'
        return adapted

    def get_tags(self) -> list:
        return list(self.TOPIC_LIBRARY['通用'])

    def get_style_rules(self) -> dict:
        return {
            '标题字数': '≤20字，自动添加Emoji前缀',
            '段落规则': '每段≤50字，自动拆分',
            '排版风格': 'Emoji分段装饰，空行分隔',
            '话题标签': '根据内容智能匹配6个热门话题',
            '互动引导': '末尾自动添加互动引导语',
            '适用场景': '图文笔记、种草推荐、生活分享'
        }

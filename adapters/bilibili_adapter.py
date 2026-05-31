"""
B站适配器 - 视频+图文风格（年轻/弹幕文化）
适配规则：
1. 标题≤20字：关键词+亮点/悬念+emoji
2. 简介≤500字：核心内容+亮点开头 → 分点+时间节点主体 → 引导三连+标签结尾
3. 字幕：每行≤15字，短句，关键信息加粗
4. 标签：#核心词 #领域 #热门
"""
import re
from .base_adapter import BaseAdapter


class BilibiliAdapter(BaseAdapter):
    platform_name = 'B站'
    platform_type = 'bilibili'
    platform_icon = '📺'
    platform_icon_url = '/static/platforms/b站.jpeg'
    title_max_length = 20
    content_max_length = 500
    platform_color = '#FB7299'
    platform_description = '视频简介风格，简洁清爽，适合UP主发布'

    # B站热门标签库
    TOPIC_LIBRARY = {
        '科技': ['#数码科技', '#科技数码', '#硬核科技', '#黑科技', '#科技分享'],
        '游戏': ['#游戏攻略', '#单机游戏', '#手游', '#游戏杂谈', '#游戏实况'],
        '学习': ['#学习打卡', '#知识分享', '#自律打卡', '#学习vlog', '#考研'],
        '生活': ['#日常vlog', '#生活碎片', '#治愈系', '#美食', '#旅行'],
        '影视': ['#影视解说', '#电影推荐', '#影评', '#追剧', '#剪辑'],
        '音乐': ['#音乐分享', '#翻唱', '#原创音乐', '#乐器', '#歌单'],
        '动漫': ['#动漫推荐', '#二次元', '#番剧', '#动漫杂谈', '#cosplay'],
        '搞笑': ['#搞笑视频', '#沙雕日常', '#整活', '#迷惑行为', '#搞笑段子'],
        '通用': ['#干货分享', '#经验分享', '#教程', '#开箱', '#测评']
    }

    def _detect_topic_category(self, content: str) -> str:
        """根据内容关键词智能匹配话题类别"""
        keywords_map = {
            '科技': ['手机', '电脑', '数码', '科技', '智能', '软件', 'app', '测评'],
            '游戏': ['游戏', '攻略', '手游', '单机', '电竞', 'LOL', '原神'],
            '学习': ['学习', '考研', '自律', '打卡', '知识', '课程', '笔记'],
            '生活': ['日常', 'vlog', '美食', '旅行', '做饭', '治愈', '开箱'],
            '影视': ['电影', '电视剧', '解说', '影评', '剪辑', '追剧'],
            '音乐': ['音乐', '翻唱', '乐器', '歌单', '原创', 'BGM'],
            '动漫': ['动漫', '二次元', '番剧', 'cos', 'ACG', '漫评'],
            '搞笑': ['搞笑', '沙雕', '整活', '迷惑', '段子', '吐槽'],
        }
        for category, keywords in keywords_map.items():
            for kw in keywords:
                if kw in content:
                    return category
        return '通用'

    def adapt_title(self, title: str) -> str:
        """B站标题：≤20字，关键词+亮点/悬念+emoji"""
        title = title.strip()
        
        # 智能添加Emoji前缀（B站风格）
        emoji_prefix_map = {
            '教程': '🔥', '干货': '💡', '攻略': '📝', '测评': '📊', '开箱': '📦',
            '推荐': '🌟', '分享': '💬', '隐藏': '🔍', '技巧': '✨', '必看': '✅',
            '新手': '👶', '入门': '🚪', '进阶': '📈', '高级': '🔝', '保姆级': '👩‍🍼',
            '手机': '📱', '电脑': '💻', '软件': '⚙️', '游戏': '🎮', '美食': '🍜',
        }
        emoji_added = False
        for keyword, emoji in emoji_prefix_map.items():
            if keyword in title:
                title = f'{emoji}{title}'
                emoji_added = True
                break
        if not emoji_added:
            title = f'🔥{title}'

        # 截断到20字
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        
        return title

    def adapt_content(self, content: str, images: list = None) -> str:
        """B站简介：≤500字，视频简介风格，简洁清爽，支持图文混排"""
        content = content.strip()
        images = images or []

        # 1. 提取核心内容作为开头
        intro = content[:100]
        # 找到第一个完整句子
        for punct in ['。', '！', '？', '；', '\n']:
            pos = intro.rfind(punct)
            if pos > 10:
                intro = intro[:pos + 1]
                break

        # 2. 生成时间节点和分点
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        time_points = []
        current_time = 0
        
        for i, para in enumerate(paragraphs[:5]):  # 最多5个时间节点
            # 提取要点
            point = para[:30].strip()
            point = re.sub(r'[。！？；,，]$', '', point)
            
            # 生成时间节点
            time_str = self._format_time(current_time)
            time_points.append(f'{time_str} {point}')
            
            # 递增时间（模拟）
            current_time += 120 + i * 60

        # 3. 组合简介内容
        time_points_str = '\n'.join(time_points)

        # 4. 添加配图标记（如果有图片）
        img_marker = ''
        if images:
            img_count = min(len(images), 3)
            img_marker = f'\n\n【配图】{"🖼️" * img_count} 共{img_count}张图片'

        # 5. 智能话题标签
        category = self._detect_topic_category(content)
        topics = self.TOPIC_LIBRARY.get(category, self.TOPIC_LIBRARY['通用'])
        topic_str = ' '.join(topics[:5])

        # 6. 结尾引导三连
        interaction_guide = '''
💪 记得点赞+投币+收藏三连支持！
📌 关注我，获取更多精彩内容
💬 欢迎在评论区留言讨论～
        '''

        # 7. 组合最终内容
        result = f'''【视频简介】
{intro}

【时间节点】
{time_points_str}{img_marker}

{topic_str}
{interaction_guide}'''

        # 8. 控制总字数≤500
        if len(result) > self.content_max_length:
            # 优先保留核心内容
            result = f'''【视频简介】
{intro}

【时间节点】
{time_points_str[:200]}

{topic_str}
💪 三连支持！📌 关注我！'''

        return result

    def _format_time(self, seconds: int) -> str:
        """格式化时间显示（如 01:20）"""
        mins = seconds // 60
        secs = seconds % 60
        return f'{mins:02d}:{secs:02d}'

    def get_tags(self) -> list:
        return list(self.TOPIC_LIBRARY['通用'])

    def get_style_rules(self) -> dict:
        return {
            '标题规则': '≤20字，关键词+亮点/悬念+emoji，如"🔥5分钟学会PS抠图"',
            '简介规则': '≤500字，核心内容+亮点开头 → 分点+时间节点主体 → 引导三连+标签结尾',
            '字幕要求': '每行≤15字，短句，关键信息加粗，适配弹幕滚动',
            '标签格式': '#核心词 #领域 #热门，如"#PS教程 #设计干货"',
            '配图要求': '横屏16:9为主，高清，适配B站页面',
            '结构要求': '开头抓眼、主体干货、结尾互动',
            '字数限制': '简介≤500字',
            '适用场景': '视频简介、图文动态、专栏文章、评论区置顶'
        }

"""
B站适配器 - 视频简介风格
适配规则：
1. 适配视频简介风格，自动精简文案
2. 自动添加适配B站的话题分区标签
3. 控制简介最大字数（2000字），避免平台截断
4. 排版简洁清爽，适配视频封面简介、评论区置顶风格
5. 自动添加时间戳标记和视频推荐引导
"""
import re
from .base_adapter import BaseAdapter


class BilibiliAdapter(BaseAdapter):
    platform_name = 'B站'
    platform_type = 'bilibili'
    platform_icon = '📺'
    title_max_length = 80
    content_max_length = 2000
    platform_description = '视频简介风格，简洁清爽，适合UP主发布'

    # B站分区标签库
    ZONE_TAGS = {
        '数码': ['#数码', '#科技', '#测评', '#数码产品', '#科技生活'],
        '游戏': ['#游戏', '#单机游戏', '#手机游戏', '#游戏推荐', '#游戏测评'],
        '生活': ['#生活', '#日常', '#vlog', '#生活方式', '#生活记录'],
        '知识': ['#知识', '#科普', '#学习', '#教程', '#干货分享'],
        '美食': ['#美食', '#料理', '#做饭', '#美食测评', '#探店'],
        '影视': ['#影视', '#电影', '#番剧', '#影视剪辑', '#影视推荐'],
        '时尚': ['#时尚', '#穿搭', '#美妆', '#护肤', '#发型'],
        '音乐': ['#音乐', '#翻唱', '#原创音乐', '#乐器', '#音乐推荐'],
        '舞蹈': ['#舞蹈', '#编舞', '#翻跳', '#舞蹈教程'],
        '鬼畜': ['#鬼畜', '#搞笑', '#沙雕', '#名场面'],
        '通用': ['#视频创作', '#UP主推荐', '#新人UP主', '#创作灵感']
    }

    def _detect_zone(self, content: str) -> str:
        """根据内容检测B站分区"""
        zone_keywords = {
            '数码': ['数码', '手机', '电脑', '耳机', '科技', '智能', 'App', '软件', '评测', '测评'],
            '游戏': ['游戏', '王者', '原神', 'LOL', '吃鸡', '手游', '端游', '主机', '电竞'],
            '生活': ['生活', '日常', 'vlog', '记录', '日记', '周末', '分享'],
            '知识': ['知识', '学习', '科普', '教程', '课程', '干货', '教学', '读书'],
            '美食': ['美食', '好吃', '做饭', '料理', '餐厅', '探店', '食谱', '烘焙'],
            '影视': ['电影', '电视剧', '番剧', '动漫', '追番', '影评', '剧情'],
            '时尚': ['穿搭', '美妆', '护肤', '化妆', '发型', '造型', '时尚'],
            '鬼畜': ['搞笑', '沙雕', '名场面', '整活', '鬼畜', '抽象'],
        }
        for zone, keywords in zone_keywords.items():
            for kw in keywords:
                if kw in content:
                    return zone
        return '通用'

    def adapt_title(self, title: str) -> str:
        """B站标题：80字以内，优化为视频标题风格"""
        title = title.strip()
        if len(title) > self.title_max_length:
            return title[:self.title_max_length - 1] + '…'
        return title

    def adapt_content(self, content: str) -> str:
        """B站简介适配：简洁清爽，视频风格"""
        content = content.strip()

        # 1. 精简文案（去除冗余描述）
        content = self._simplify_content(content)

        # 2. 格式化简介结构
        content = self._format_description(content)

        # 3. 控制总字数（B站简介限制2000字）
        if len(content) > self.content_max_length:
            # 智能截断：在完整段落处截断
            truncated = content[:self.content_max_length - 50]
            last_period = max(
                truncated.rfind('。'),
                truncated.rfind('\n\n'),
                truncated.rfind('！'),
                truncated.rfind('？')
            )
            if last_period > self.content_max_length // 2:
                content = truncated[:last_period + 1]
            else:
                content = truncated
            content += '\n\n……\n（简介字数已达上限，完整内容请看视频~）'

        # 4. 添加B站分区标签
        zone = self._detect_zone(content)
        tags = self.ZONE_TAGS.get(zone, self.ZONE_TAGS['通用'])
        tag_str = ' '.join(tags[:5])

        # 5. 添加UP主标准引导
        cta = (
            '\n\n━━━━━━━━━━━━━━━━━━\n'
            '👍 喜欢本期视频记得【点赞】【投币】【收藏】！\n'
            '🔔 关注我，第一时间获取更新通知\n'
            '💬 有什么想法欢迎评论区留言讨论~'
        )

        adapted = f'{content}\n\n{tag_str}{cta}'
        return adapted

    def _simplify_content(self, content: str) -> str:
        """精简文案，保留核心信息"""
        # 移除重复换行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 移除过长的修饰性描述（超过100字的超长句进行拆分）
        lines = content.split('\n')
        simplified = []
        for line in lines:
            line = line.strip()
            if not line:
                simplified.append('')
                continue
            # 超长行按标点拆分
            if len(line) > 100:
                parts = re.split(r'([。！？；])', line)
                merged = []
                current = ''
                for part in parts:
                    current += part
                    if part in '。！？；' and len(current) > 30:
                        merged.append(current)
                        current = ''
                if current:
                    merged.append(current)
                simplified.extend(merged)
            else:
                simplified.append(line)

        return '\n'.join(simplified)

    def _format_description(self, content: str) -> str:
        """格式化B站简介结构"""
        lines = content.split('\n')
        formatted = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted.append('')
                continue
            formatted.append(stripped)

        # 在合适位置插入时间戳标记（如果内容较长）
        result = '\n'.join(formatted)
        if len(result) > 500:
            result = re.sub(
                r'\n\n',
                '\n\n',
                result
            )

        return result

    def get_tags(self) -> list:
        return self.ZONE_TAGS['通用']

    def get_style_rules(self) -> dict:
        return {
            '标题字数': '≤80字',
            '简介字数': '≤2000字（平台限制）',
            '排版风格': '简洁清爽，视频简介风',
            '分区标签': '根据内容智能匹配B站分区话题',
            '互动引导': '标准UP主三连引导',
            '适用场景': '视频简介、评论区置顶、动态发布'
        }

# 自媒体多平台分发工具

---

## 🎥 B站视频演示地址

> ⚠️ **请在此处填写您的B站视频地址**
> 
> [点击观看演示视频](https://www.bilibili.com/video/)
> 
> 或直接输入视频链接: 
> ```
> https://www.bilibili.com/video/BVxxxxxxxxxx/
> ```

---

一款帮助自媒体创作者实现一次内容输入、自动适配多平台格式并模拟发布的工具。

## ✨ 功能特性

- **图文混排编辑**: 支持文字与图片混合输入，类似 Word 的编辑体验
- **图片编辑**: 支持拖拽移动位置、调整大小，类似 PPT 操作
- **多平台适配**: 自动将内容适配为小红书、公众号、知乎、B站等平台格式
- **模拟发布**: 支持模拟发布到各平台，包含违规词检测
- **可扩展架构**: 插件化设计，方便添加新平台

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Flask 2.0+
- 数据库: SQLite (默认) / MySQL

### 安装运行
```bash
# 进入项目目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py
```

## 📦 支持平台

| 平台 | 类型 | 状态 |
|------|------|------|
| 小红书 | 图文笔记 | ✅ |
| 微信公众号 | 长文推送 | ✅ |
| 知乎 | 问答/文章 | ✅ |
| B站 | 视频简介 | ✅ |
| 微博 | 社交媒体 | ✅ |

## 📁 项目结构

```
backend/
├── adapters/          # 平台适配器
│   ├── base_adapter.py      # 适配器基类
│   ├── xiaohongshu_adapter.py
│   ├── wechat_adapter.py
│   ├── zhihu_adapter.py
│   ├── bilibili_adapter.py
│   └── ...
├── routes/            # 路由模块
│   ├── auth.py         # 认证路由
│   ├── publish.py      # 发布路由
│   └── platforms.py    # 平台管理
├── models/            # 数据库模型
├── static/            # 静态资源
│   └── platforms/      # 平台图标
├── templates/         # HTML模板
│   └── publish.html    # 发布页面
├── app.py             # 应用入口
└── requirements.txt   # 依赖清单
```

## 🔧 配置说明

### 数据库配置
默认使用 SQLite，如需使用 MySQL，请设置环境变量：
```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost/db_name"
```

### 平台扩展
在 `adapters/` 目录下创建新的平台适配器即可扩展支持新平台。

## 📝 使用说明

1. **输入内容**: 在编辑器中输入标题和正文，可插入图片
2. **选择平台**: 选择要发布的目标平台
3. **预览适配**: 点击预览查看各平台适配效果
4. **模拟发布**: 点击发布进行模拟发布测试

## 📄 许可证

MIT License

---

*如有问题或建议，欢迎提交 Issue 或 PR！*

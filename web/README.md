# 凡人修仙传 RAG 检索系统

基于《凡人修仙传》内容的智能检索与问答系统，使用 React + TypeScript + Tailwind CSS 构建。

## 技术栈

- **框架**: React 19 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **包管理**: Bun
- **开发服务器**: Vite Dev Server

## 快速开始

### 安装依赖

```bash
bun install
```

### 启动开发服务器

```bash
bun run dev
```

应用将在 `http://localhost:3000` 上运行。

### 构建生产版本

```bash
bun run build
```

### 预览生产版本

```bash
bun run preview
```

## 项目结构

```
web/
├── src/
│   ├── components/         # React 组件
│   │   ├── SearchHistory.tsx    # 搜索历史组件
│   │   ├── SearchResults.tsx    # 搜索结果组件
│   │   └── mockData.ts          # 模拟数据
│   ├── App.tsx            # 主应用组件
│   ├── main.tsx           # 入口文件
│   └── styles.css         # 样式文件
├── index.html             # HTML 模板
├── vite.config.ts        # Vite 配置
├── tailwind.config.js    # Tailwind CSS 配置
├── postcss.config.js     # PostCSS 配置
└── package.json          # 项目依赖
```

## 主要功能

1. **搜索功能**: 支持关键词搜索，实时过滤结果
2. **搜索历史**: 自动保存搜索历史，支持快速重复搜索
3. **AI 摘要**: 提供智能搜索摘要和关键点
4. **排序功能**: 支持按相关性排序（升序/降序）
5. **响应式设计**: 适配不同屏幕尺寸

## 组件说明

### SearchHistory
- 管理搜索历史记录
- 支持删除单个历史项
- 支持清空所有历史

### SearchResults
- 显示搜索结果列表
- 处理用户交互（查看详情、相关推荐）
- AI 摘要展示
- 排序功能

### App
- 主应用组件，协调各个子组件
- 管理全局状态（搜索词、结果、加载状态等）

## 开发说明

项目使用 Vite 作为构建工具，支持热更新。Tailwind CSS 用于样式管理，提供了现代化的 UI 组件样式。

搜索功能目前使用模拟数据，实际应用中可以替换为真实的 API 调用。
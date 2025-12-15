# EPUB 阅读器系统

一个轻量级的 EPUB 转 Markdown 工具，配合静态网页阅读器，使用 localStorage 追踪阅读进度。

## 项目结构

```
Reader/
├── index.html                 # 书架页（主页）
├── books.json                 # 书籍目录（手动维护）
├── epub_to_md_gui.py         # EPUB 转 Markdown 工具（Tkinter 图形界面）
├── reader/                    # 阅读器网页界面
│   ├── book.html             # 书籍目录页
│   ├── chapter.html          # 章节阅读页
│   ├── styles.css            # 样式文件
│   └── reader.js             # 阅读进度工具函数
└── books_src/                 # 书籍库（由转换工具生成）
    └── {book_id}/            # 每本书一个文件夹，例如：books_src/anki-manual/
        ├── meta.json         # 书籍元数据
        ├── *.md              # 章节 Markdown 文件
        └── assets/           # 图片和资源文件
```

## 第一部分：EPUB 转 Markdown 转换工具

### 依赖安装

**无需手动安装！** 程序会自动检测并安装所需的 Python 库。

首次运行时，程序会自动安装 `html2text` 库。

### 使用方法

1. **Run the converter:**

```bash
python epub_to_md_gui.py
```

2. **选择 EPUB 文件：**
   - 点击 "Select EPUB Files" 按钮
   - 选择一个或多个 `.epub` 文件
   - 工具会自动处理所有选中的文件

3. **转换输出：**
   - 每本书转换到 `books_src/{book_id}/` 目录
   - Markdown 文件命名格式：`{序号:02d}-{书名slug}--{章节slug}.md`
   - 图片等资源保存到 `books_src/{book_id}/assets/`
   - 元数据保存到 `books_src/{book_id}/meta.json`
   - **标题提取**：自动提取所有连续的标题标签（h1-h6），组合成完整标题
   - **层级前缀**：根据标题级别自动添加前缀（h2 加 `-`，h3 加 `--`，以此类推）

4. **自动更新 books.json：**
   - 程序自动将新书信息添加到 `books.json` 文件的开头
   - 无需手动复制粘贴

### 如何找到转换后的书籍文件

转换完成后，每本书都在独立的文件夹中：

```
books_src/
├── anki-manual/              ← 书名：Anki Manual
│   ├── meta.json            ← 元数据（包含章节列表）
│   ├── 01-anki-manual--getting-started.md
│   ├── 02-anki-manual--decks.md
│   └── assets/              ← 图片资源
│       ├── image1.png
│       └── image2.jpg
│
├── python-cookbook/          ← 书名：Python Cookbook
│   ├── meta.json
│   ├── 01-python-cookbook--data-structures.md
│   └── assets/
│
└── 另一本书的拼音或英文名/     ← 每本书一个文件夹
```

**如何找到某本具体的书：**
1. 打开 `books_src/` 文件夹
2. 文件夹名就是书名的 slug（小写、空格变减号）
3. 例如：
   - "Anki Manual" → `books_src/anki-manual/`
   - "Python Cookbook" → `books_src/python-cookbook/`
   - "深入理解计算机系统" → `books_src/深入理解计算机系统/`

### 文件命名规则

**书籍 ID (book_slug)：**
- 从书名自动生成
- 小写字母，空格替换为减号
- 移除特殊字符
- **长度限制：最多 50 字符**，超出部分直接截断
- 示例："Anki Manual" → "anki-manual"

**章节文件：**
- 格式：`{序号:02d}-{书名slug}--{章节slug}.md`
- 示例：`01-anki-manual--getting-started.md`
- 序号补零到 2 位数字
- **章节 slug 最多 10 字符**，超出部分直接截断
- **总文件名长度限制：150 字符**

**章节 ID：**
- 格式：`{序号:02d}-{章节slug}`
- 示例：`01-getting-started`
- 用于 URL 和 localStorage 键名

**长度限制说明：**
- 书籍文件夹名（book_id）：最多 50 字符
- 章节 slug：最多 10 字符
- 作者 slug（如使用）：最多 10 字符
- 完整文件名：最多 150 字符
- 所有超长部分自动截断，确保末尾不含连字符

### meta.json 格式

```json
{
  "book_id": "anki-manual",
  "title": "Anki Manual",
  "author": "Some Author",
  "chapters": [
    {
      "chapter_id": "01-getting-started",
      "order": 1,
      "title": "Getting Started",
      "markdown_file": "01-anki-manual--getting-started.md"
    },
    {
      "chapter_id": "02-chapter-1",
      "order": 2,
      "title": "CHAPTER 1\nThe Adult Playground",
      "markdown_file": "02-anki-manual--chapter-1.md"
    },
    {
      "chapter_id": "03-part-1",
      "order": 3,
      "title": "-PART 1\nIntroduction",
      "markdown_file": "03-anki-manual--part-1.md"
    }
  ]
}
```

**标题说明：**
- **无前缀**：h1 级标题（顶级章节，如 "Getting Started"）
- **一个 `-` 前缀**：h2 级标题（二级标题，如 "-CHAPTER 1"）
- **两个 `--` 前缀**：h3 级标题（三级标题）
- **多行标题**：同一章节的多个连续标题会用换行符 `\n` 组合（如 "CHAPTER 1\nThe Adult Playground"）

### books.json 格式

项目根目录的 `books.json` 文件包含书籍列表数组：

```json
[
  {
    "book_id": "anki-manual",
    "title": "Anki Manual",
    "author": "Some Author",
    "description": "可选的描述",
    "meta_path": "books_src/anki-manual/meta.json"
  }
]
```

## 第二部分：静态网页阅读器

### 运行阅读器

1. **打开阅读器：**
   - 直接用浏览器打开 `index.html`
   - 或使用本地服务器（推荐）：

```bash
# Python 3
python -m http.server 8000

# 然后打开 http://localhost:8000
```

2. **导航：**
   - 书架页 (`index.html`) → 显示所有书籍
   - 书籍目录 (`reader/book.html?book_id=xxx`) → 章节列表
   - 章节页 (`reader/chapter.html?book_id=xxx&chapter_id=xxx`) → 阅读章节

### 功能特性

**书架页 (index.html)：**
- 显示 `books.json` 中的所有书籍
- 如有阅读进度，显示"继续阅读"按钮
- 链接到书籍目录页

**书籍目录页 (book.html)：**
- 列出 `meta.json` 中的所有章节
- "继续阅读"按钮跳转到上次阅读的章节
- 显示章节编号和标题

**章节阅读页 (chapter.html)：**
- 左侧边栏：目录，当前章节高亮显示
- 主体区域：渲染后的 Markdown 内容
- 上一章/下一章导航
- 自动恢复滚动位置
- 每 500 毫秒保存一次阅读进度

### 阅读进度（localStorage）

系统使用 localStorage 追踪阅读进度：

**键名：**
- `reading_progress::{book_id}::{chapter_id}` → `{ scrollY, timestamp }`
- `last_opened_chapter::{book_id}` → `{ chapter_id, timestamp }`

**工具函数（在 reader.js 中）：**
- `saveScrollPosition(bookId, chapterId, scrollY)` - 保存滚动位置
- `getScrollPosition(bookId, chapterId)` - 获取保存的滚动位置
- `restoreScrollPosition(bookId, chapterId)` - 页面加载时恢复滚动
- `saveLastOpenedChapter(bookId, chapterId)` - 保存最后打开的章节
- `getLastOpenedChapter(bookId)` - 获取最后打开的章节
- `clearBookProgress(bookId)` - 清除某本书的所有进度

### 响应式设计

**桌面端 (>768px)：**
- 侧边栏始终可见，显示完整目录
- 点击侧边栏右上角的 `×` 按钮可以折叠侧边栏
- 侧边栏折叠后，屏幕左侧出现展开按钮 `›`，点击可重新展开
- 平滑的宽度过渡动画

**平板端 (769px - 1024px)：**
- 同桌面端逻辑，侧边栏宽度为 250px（比桌面略窄）
- 支持折叠和展开

**移动端 (≤768px)：**
- 侧边栏默认隐藏在屏幕左侧
- 右下角悬浮按钮 `☰` 用于打开侧边栏
- 点击侧边栏的 `×` 按钮、内容区域或目录项时自动关闭
- 侧边栏从左侧平滑滑入/滑出

**窗口大小变化：**
- 自动处理桌面和移动端之间的切换
- 状态恢复正确，无遗留问题

## 使用流程

1. **添加书籍：**
   ```
   运行 epub_to_md_gui.py
   → 选择 EPUB 文件
   → 文件转换到 books_src/
   → 自动更新 books.json（新书添加到开头）
   ```

2. **阅读书籍：**
   ```
   打开 index.html
   → 选择一本书
   → 查看目录
   → 阅读章节
   → 进度自动保存
   ```

3. **继续阅读：**
   ```
   返回书架
   → 有进度的书显示"继续阅读"按钮
   → 直接跳转到上次阅读的章节和滚动位置
   ```

## 依赖项

**Python 工具：**
- Python 3.6+
- `html2text` 库（自动安装）
- `tkinter`（通常随 Python 自带）

**网页阅读器：**
- 支持 localStorage 的现代浏览器
- `marked.js`（从 CDN 加载，用于 Markdown 渲染）

## 转换器功能详解

### 标题提取和处理

转换器会自动从 EPUB 章节中提取完整的标题信息：

1. **完整标题提取**
   - 提取所有连续的标题标签（h1 到 h6）
   - 多个标题用换行符组合成完整标题
   - 示例：一个章节有标题 "CHAPTER 1" 和副标题 "The Adult Playground"，会合并为 "CHAPTER 1\nThe Adult Playground"

2. **层级前缀**
   - 根据最高标题级别自动添加前缀
   - 用于在目录中区分标题的层级结构
   - h1（顶级）：无前缀
   - h2（二级）：`-` 前缀
   - h3（三级）：`--` 前缀
   - h4 及以下：依次增加更多 `-`

## 注意事项

- 转换器自动提取所有连续的标题标签，保留多级标题结构
- 根据标题级别（h1/h2/h3...）自动添加层级前缀，方便在目录中显示结构
- 图片提取到 `assets/` 目录，Markdown 中的路径会自动修正
- 无需后端服务器 - 一切都在客户端运行
- 阅读进度保存在浏览器本地
- 每本书都在独立的目录中自包含

## 常见问题

**Python 工具无法启动：**
- 程序会自动安装依赖，如果失败请检查网络连接
- 检查 Python 版本：`python --version`（需要 3.6+）

**未找到章节：**
- 某些 EPUB 的结构不标准
- 查看转换器 GUI 中的日志了解错误信息

**网页无法加载：**
- 确保所有文件都在正确的目录中
- 检查浏览器控制台（F12）查看错误
- 确保 `books.json` 是有效的 JSON 格式

**图片不显示：**
- 检查图片是否在 `books_src/{book_id}/assets/` 目录中
- 验证 Markdown 中的图片路径以 `assets/` 开头

**如何找到转换后的某本书：**
- 打开 `books_src/` 文件夹
- 文件夹名称就是书名的 slug（例如：books_src/anki-manual/）
- 或者打开 `books.json` 查看 `meta_path` 字段

## 许可

这是一个简单的教育工具，使用需自行斟酌。

# Deli Cai — 个人主页

本站基于 [xbpeng/xbpeng.github.io](https://github.com/xbpeng/xbpeng.github.io) 模版搭建。
`css/main.css`、`_includes/`、`_layouts/` 均与模版逐字节一致，只做了两类改动：

1. **替换文字**：姓名、邮箱、简介、论文、站点标题等全部换成本人的信息。
2. **删除原作者的内容**：Team / Teaching / Art 三个页面及其导航链接、Codebase 和 Thesis 两个面板、
   Prospective students 按钮、Twitter 账号，以及原作者的 Google Analytics 统计代码。

除此之外，模版原有的 HTML 结构、class、CSS 一律未动。

## 目录结构

```
_config.yml              站点标题、描述、网址
index.html               首页（个人简介 + 论文列表）
_data/publications.yml   论文的年份分组与显示顺序
_includes/               页面片段
  publication.html         首页中单条论文的渲染方式
  meta.html                <meta> 标签（分享预览、Google Scholar 抓取）
  small_image.html         自动查找 xxx_small.jpg 缩略图
  icon.html                按钮上的小图标
_layouts/
  default.html             全站外框（顶部导航在这里）
  project.html             单篇论文详情页的外框
css/main.css             全部样式（与模版完全一致，含深色模式）
images/cmc.jpg           首页照片占位图
docs/Deli_Cai_CV.pdf     CV，首页 “CV” 按钮指向它
projects/<论文名>/        每篇论文一个目录（含 index.html 和 cmc.jpg 占位图）
```

## 常见修改

### 改首页文字
编辑 [index.html](index.html)。照片、邮箱、简介都在这个文件里。

### 改站点标题和描述
编辑 [_config.yml](_config.yml)。`description` 会出现在搜索结果和分享卡片里。

### 改论文顺序 / 增删论文
编辑 [_data/publications.yml](_data/publications.yml)。`projects` 里每一项都必须对应 `projects/` 下的一个目录名，
否则首页会出现红色的 `Missing project page` 提示。

### 替换占位图
五篇论文目前都各自用自己目录里的 `cmc.jpg` 当占位图，首页照片用的是 `images/cmc.jpg`。

- 替换某篇论文的图：把新图放进该论文目录，然后在同目录 `index.html` 里改 `thumbnail` 和 `teaser` 两行：

  ```yaml
  thumbnail: "StereoGS_thumb.png"    # 首页列表里的 200px 小图
  teaser: "StereoGS_teaser.png"      # 详情页顶部的大图
  ```

  图片文件名不带 `/`，就是相对于该论文自己的目录。如果同时放了 `StereoGS_thumb_small.jpg`，
  首页会自动优先用它以加快加载。
- 替换首页照片：直接覆盖 `images/cmc.jpg`。

### 补充论文的摘要 / PDF / BibTeX
每个 `projects/<论文名>/index.html` 的 front matter 里都留好了注释示例，把 `#` 去掉填入内容即可：

```yaml
paper: "StereoGS_2026.pdf"     # 把 PDF 放进同一目录，Paper 按钮会自动出现
abstract: >-
  摘要正文。想分多段就用单独一行 | 分隔。
bibtex: |
  @inproceedings{...}
```

**填了才显示，没填就不显示** —— 这样不会在页面上留下空的 Abstract 标题或空 BibTeX 框。

### 改顶部导航
编辑 [_layouts/default.html](_layouts/default.html)。目前只有「Home」一项，
因为模版原有的 Team / Teaching / Art 三个页面属于原作者、已经删除。

## 本地预览

需要 Ruby + Jekyll：

```bash
gem install bundler jekyll
bundle exec jekyll serve
```

然后打开 http://localhost:4000 。如果只是改文字，直接在 GitHub 网页上改也能生效，不必装环境。

## 部署

推送到 `master` 分支后，在仓库 **Settings → Pages** 里把 Source 设为 `Deploy from a branch`，
分支选 `master`、目录选 `/ (root)`。站点地址：<https://cdlchoi.github.io>

## 还没填的内容

- **首页照片**：现在用的是论文占位图。模版 `.intro-photo` 固定 150px 宽、高度自适应，
  `cmc.jpg` 是 4685×1257 的横长图，会显示成一条细带。**换一张竖版证件照即可正常显示。**
- **论文摘要、PDF、BibTeX**：五篇都还没填。
- **两篇待投稿论文（2027）的作者列表**：CV 里只写了合作者、没有确定作者顺序，所以先留空了，
  确认后填 `authors` 即可（详情页现在显示的是 `author_note` 里的合作说明）。
- **Google Scholar / ORCID / X 等链接**：CV 里没有，所以没加。有的话加到首页 `profile-links` 里。

## 与模版代码的唯一差异（共 5 处 `{% if %}` 判断）

为了让「还没填内容」的字段不产生空的标题和失效按钮，加了几处条件判断。
模版本身就有大量同类写法（如 `{% if page.award %}`、`{% if page.videos %}`），所以风格是统一的：

| 文件 | 改动 |
| --- | --- |
| `_layouts/project.html` | Paper 按钮、Abstract 分区、BibTeX 分区各包一层 `{% if %}` |
| `_includes/publication.html` | 首页条目的 Paper 按钮包一层 `{% if pub.paper %}` |
| `_includes/meta.html` | `citation_pdf_url` 包一层 `{% if page.paper %}` |

排版、class、CSS 均未改动。

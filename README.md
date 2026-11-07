# 图片信息与简单编辑工具

一个使用 Python 编写的**命令行**图片工具，可以读取图片的基础信息，并完成缩放、裁剪、旋转、翻转、灰度化和格式转换等简单编辑。

所有编辑结果都会保存为新文件，不会覆盖原图。

## 功能一览

| 功能 | 说明 |
| --- | --- |
| 读取图片信息 | 显示文件名、图片格式、宽度、高度、颜色模式、文件大小（KB/MB，保留两位小数） |
| 缩放 | 指定宽度和高度；只给宽度或高度时按原比例缩放 |
| 裁剪 | 指定左、上、右、下坐标；区域越界时给出明确提示 |
| 旋转 | 支持 90、180、270 度，也支持其他顺时针角度 |
| 翻转 | 支持水平翻转、垂直翻转和同时翻转 |
| 灰度化 | 把彩色图片转换为灰度图片 |
| 格式转换 | 支持 PNG、JPG/JPEG、WEBP、BMP 之间互相转换 |

## 环境配置

### 运行环境

- Python 3.10 及以上
- Pillow（图片处理库）
- 依赖配置见 `pyproject.toml`，锁定版本见 `uv.lock`

### 方式一：使用 uv（推荐）

1. 安装 uv（如果还没有安装）：

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   如果系统已经安装 Python 和 pip，也可以直接执行：

   ```bash
   python -m pip install uv
   ```

2. 在项目根目录安装依赖：

   ```bash
   uv sync
   ```

   该命令会自动创建 `.venv` 虚拟环境，并按照 `uv.lock` 安装 Pillow 和本项目。

### 方式二：使用 pip + venv

如果不想使用 uv，也可以使用 Python 自带的虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用：.venv\Scripts\activate
python -m pip install -e .
```

## 运行方式

以下命令都在**项目根目录**执行。使用 uv 时，在命令前加 `uv run` 即可。

查看帮助：

```bash
uv run imagetool --help
```

如果不使用 uv，先激活虚拟环境，然后使用：

```bash
imagetool --help
# 或者
python -m image_tool --help
```

### 1. 读取图片信息

```bash
uv run imagetool info demo.jpg
```

示例输出：

```text
文件名：demo.jpg
图片格式：JPEG
宽度：1920 像素
高度：1080 像素
颜色模式：RGB
文件大小：245.32 KB（251199 字节）
```

### 2. 缩放图片

指定宽度，高度会按原比例自动计算：

```bash
uv run imagetool resize demo.jpg --width 800
```

指定高度：

```bash
uv run imagetool resize demo.jpg --height 600
```

同时指定宽度和高度（按指定尺寸缩放）：

```bash
uv run imagetool resize demo.jpg --width 800 --height 600
```

示例输出：

```text
已保存到：/home/user/pictures/demo_resized.jpg
```

### 3. 裁剪图片

使用左、上、右、下四个坐标指定裁剪区域（单位：像素）：

```bash
uv run imagetool crop demo.jpg --left 100 --top 50 --right 900 --bottom 650
```

如果区域超出图片范围，程序会给出提示，例如：

```text
错误：裁剪区域不合法：left=0, top=0, right=999, bottom=70，图片尺寸为 120x80。要求 0 <= left < right <= 120 且 0 <= top < bottom <= 80。
```

### 4. 旋转图片

顺时针旋转 90 度：

```bash
uv run imagetool rotate demo.jpg --angle 90
```

也支持 180、270 度以及其他角度：

```bash
uv run imagetool rotate demo.jpg --angle 180
uv run imagetool rotate demo.jpg --angle 45
```

### 5. 翻转图片

水平翻转：

```bash
uv run imagetool flip demo.jpg --direction horizontal
```

垂直翻转：

```bash
uv run imagetool flip demo.jpg --direction vertical
```

同时水平和垂直翻转：

```bash
uv run imagetool flip demo.jpg --direction both
```

### 6. 灰度化

```bash
uv run imagetool grayscale demo.jpg
```

### 7. 格式转换

PNG 转 JPG：

```bash
uv run imagetool convert demo.png --to jpg
```

JPG 转 PNG：

```bash
uv run imagetool convert demo.jpg --to png
```

支持的格式：`png`、`jpg`、`jpeg`、`webp`、`bmp`。

### 8. 指定输出文件

以上所有编辑命令都可以使用 `-o` 或 `--output` 指定保存位置：

```bash
uv run imagetool resize demo.jpg --width 800 -o output/demo_small.jpg
```

如果不指定 `-o`，程序会在原图旁边生成新文件，命名规则为：

- 缩放：`原文件名_resized.原扩展名`
- 裁剪：`原文件名_cropped.原扩展名`
- 旋转：`原文件名_rotated.原扩展名`
- 翻转：`原文件名_flipped.原扩展名`
- 灰度化：`原文件名_gray.原扩展名`
- 格式转换：`原文件名_converted.目标扩展名`

如果同名文件已经存在，会自动追加 `_1`、`_2` 等序号，避免误覆盖。

## 通用规则

1. **不覆盖原图**：输出文件不能与原图路径相同；默认输出文件名也会自动避开已有文件。
2. **错误提示**：文件不存在、文件不是有效图片、宽高小于等于 0、裁剪区域越界、输出格式无法识别等情况都会给出中文提示，程序不会直接崩溃。
3. **透明通道处理**：带透明通道的 PNG 转换为 JPG 时，会先合成到白色背景并转换为 RGB，避免透明区域变黑。
4. **保存位置**：每次保存成功后都会打印完整的输出路径。

## 项目结构

```text
image-tool/
├── pyproject.toml          # 项目配置和依赖
├── uv.lock                 # uv 依赖锁定文件
├── README.md               # 说明文件
├── .gitignore              # 忽略虚拟环境、缓存等文件
├── src/
│   └── image_tool/
│       ├── __init__.py
│       ├── __main__.py     # 支持 python -m image_tool
│       ├── cli.py          # 命令行参数解析和各命令入口
│       └── core.py         # 图片读取、编辑和保存的核心函数
└── tests/
    └── test_core.py        # 核心功能单元测试
```

## 运行测试

```bash
uv run python -m unittest discover -s tests -v
```

## Git 分支说明

- `main`：最终可运行版本
- `dev`：功能开发分支，开发完成后合并到 `main`

## 常见问题

**提示“文件不存在”**

请检查图片路径是否正确；包含空格的路径建议用引号包起来，例如：

```bash
uv run imagetool info "my photos/demo.jpg"
```

**提示“不是有效的图片文件”**

文件扩展名可能是图片，但内容已损坏或并不是真正的图片。请换一张图片重试。

**提示“无法根据扩展名确定图片格式”**

请使用 `-o` 指定带有支持扩展名的输出文件，例如 `-o result.png` 或 `-o result.jpg`。

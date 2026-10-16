# Orwell: Ignorance is Strength 中文测试包构建工具

本项目对应仓库 **quellah1010-code/Orswell-ingnorance**：
https://github.com/quellah1010-code/Orswell-ingnorance

目前仅交付已有的 0.1 小样：11 条开场介绍对白（含不同分支）和 3 条早期任务，共 14 条文本，以及覆盖这些译文的中文备用字库。**这不是完整第一章或全游戏汉化。** 此次整理只解决源码交付和本地重建，没有增加汉化范围。

仓库保存 Python 工具、中文译文映射、依赖版本和构建说明。游戏 DLL、assets、原文全集、生成的补丁包均不入库。译文映射仅保存资源编号、原文哈希和中文译文；构建时从你的本地游戏文件读取原文。

## 在 Windows 本地生成 ZIP

需要 Python 3.12，以及你自己的 Windows Steam 版游戏文件。以下命令在下载或克隆本仓库后的根目录中，用 PowerShell 执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools/build_preview.py --game-dir "E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength"
```

把游戏路径改成自己的实际路径。脚本只读取游戏目录，不会自动安装或替换游戏文件。它会下载开放许可的 Noto CJK 字体并核对 SHA-256，生成本地文件：

```text
build/preview-0.1/orwell-zh-preview-0.1.zip
```

若已经替换过游戏的 `resources.assets`，请用原版备份构建：

```powershell
.\.venv\Scripts\python.exe tools/build_preview.py --resources "E:\备份\resources.assets"
```

输入文件必须匹配本次测试的版本，SHA-256 为：

```text
1bc553fdc10358d2a4f78de1e2079a61ee46dc993636403dcfbc7b052b607b78
```

不匹配时脚本会停止。已有输出目录也不会被覆盖；重复构建可传入新的 `--output build/preview-0.1-rebuild`。若已有相同版本的字体，可用 `--font-file` 指定；仍会校验字体哈希。

Linux 使用同一个入口：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_preview.py --resources /path/to/original/resources.assets
```

## 安装和验证

阅读 [测试包安装及还原说明](docs/preview-install.txt)。退出游戏，备份原 `resources.assets`，然后手动安装生成的文件。测试位置是能力测试结束后的安普尔福德开场介绍及三个早期任务；主菜单和其他大部分文本仍为英文。

资源回填、对象引用、字库覆盖和贴图重新读取已在 Linux/Python 3.12 中验证。构建脚本检查生成资源是否与已有小样逐字节一致；**尚未完成 Windows 构建及游戏内显示、换行、交互验证**。原始 ZIP 的完整性记录见 [交付校验记录](docs/delivery-verification.json)。新 ZIP 使用固定元数据，ZIP 哈希可能与原压缩包不同，内部游戏资源哈希必须相同。

## 文件说明

- `translations/preview.zh-CN.json`：14 条中文译文、稳定编号和原文校验值。
- `tools/build_preview.py`：从本地原版资源生成现有小样的完整入口。
- `tools/orwell_resources.py`：已验证的三类文本提取和回填工具。
- `tools/build_preview_font.py`：生成小样使用的静态 TextMesh Pro 中文备用字库。
- `tools/inspect_assembly.py`：静态读取托管程序集元数据，不运行游戏 DLL。
- `licenses/Noto-OFL.txt`：所用开放字体的 SIL OFL 1.1 许可。

`build/` 中的文件包含从本地游戏生成的资源，仅用于本地安装测试。请保持 `.gitignore` 中的游戏资源、字体缓存和输出目录排除规则，不将它们提交到仓库或发布为公开附件。

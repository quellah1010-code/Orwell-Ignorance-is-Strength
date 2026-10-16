# Orwell: Ignorance is Strength 中文测试包构建工具

本项目对应仓库 **quellah1010-code/Orwell-Ignorance-is-Strength**：
https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength

原仓库地址 `quellah1010-code/Orswell-ingnorance` 已由 GitHub 重定向到上述新名称；这里的下载和教程链接均使用新地址。

目前仅交付已有的 0.1 小样：11 条开场介绍对白（含不同分支）和 3 条早期任务，共 14 条文本，以及覆盖这些译文的中文备用字库。**这不是完整第一章或全游戏汉化。** 此次整理只解决源码交付和本地重建，没有增加汉化范围。

仓库保存 Python 工具、中文译文映射、依赖版本和构建说明。游戏 DLL、assets、原文全集、生成的补丁包均不入库。译文映射仅保存资源编号、原文哈希和中文译文；构建时从你的本地游戏文件读取原文。

## 下载工具和查看教程

教程和工具位于默认的 `main` 分支，打开仓库首页即可看到这份 README。

- [打开仓库首页及教程](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/tree/main)
- [直接下载源码 ZIP](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/archive/refs/heads/main.zip)

下载的是构建工具，不能直接覆盖到游戏里。下面会用你电脑上已经安装的原版游戏，在本地生成可安装的测试包。**不需要安装 Git，也不需要配置云环境或操作 PR。**

## Windows：从下载到安装，一步一步做

### 1. 下载并解压工具

点击上面的“直接下载源码 ZIP”，下载后右键 ZIP →“全部提取”。

打开解压后的文件夹，直到能同时看到 `README.md`、`requirements.txt`、`tools` 和 `translations`。后面的命令都在这个文件夹里执行。不要在尚未解压的 ZIP 窗口里操作，也不要把整个源码文件夹复制进游戏目录。

### 2. 安装 Python 3.12

打开 [Python 3.12.10 官方下载页](https://www.python.org/downloads/release/python-31210/)，在页面下方 Files 中选择 **Windows installer (64-bit)**，下载并运行。

在安装窗口勾选 **Add python.exe to PATH**，保留 Python Launcher（`py` 启动器）的安装选项，然后点击 Install Now。已经安装 Python 3.12 的话，可以直接验证下一步。

### 3. 在工具文件夹打开 PowerShell

在第 1 步解压后的文件夹里，点击资源管理器上方的地址栏，输入 `powershell` 并按回车。会打开命令窗口；不需要管理员权限。

复制下面这行，粘贴到命令窗口并按回车：

```powershell
py -3.12 --version
```

应该显示 `Python 3.12.x`。如果提示找不到 `py` 或没有 Python 3.12，先完成第 2 步，关闭命令窗口，再按本步骤重新打开。

### 4. 逐条运行这三条命令

**每次复制一条，按回车，等运行结束后再执行下一条。** 如果某一步报错，先停下来，不要继续安装补丁。

第一条，创建工具运行环境：

```powershell
py -3.12 -m venv .venv
```

第二条，下载所需依赖，需要联网：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

第三条，读取本地原版游戏并生成测试包。下面已经填入你截图里的游戏位置；如果后来移动了游戏，修改引号内的路径：

```powershell
.\.venv\Scripts\python.exe tools/build_preview.py --game-dir "E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength"
```

首次运行还会下载并校验 Noto CJK 开放字体。这个命令只读取游戏目录，**不会自动替换游戏文件**。末尾显示 `Local ZIP:` 及 ZIP 路径才表示构建完成；它不代表游戏内测试已经通过。

回到工具文件夹，依次打开 `build` → `preview-0.1`，可以找到：

```text
orwell-zh-preview-0.1.zip
```

这才是本地生成的安装测试包。

### 5. 备份原文件，再安装测试包

1. 完全退出游戏。
2. 在 Steam 游戏库中右键游戏 →“管理”→“浏览本地文件”，再打开 `Ignorance_Data`。
3. 将里面的原版 `resources.assets` **复制到游戏目录外的备份文件夹**，例如桌面的“Orwell 原版备份”。确认备份文件确实存在后再继续。
4. 解压刚生成的 `orwell-zh-preview-0.1.zip`。在解压内容里找到 `Ignorance_Data/resources.assets`，复制到游戏的 `Ignorance_Data` 文件夹，同意替换同名文件。
5. 启动游戏，选择英文语言。进入能力测试结束后的安普尔福德开场介绍，检查中文显示。

**主菜单、网页、邮件及大部分对白仍为英文，这是当前 14 条小样的范围。** 检查中文有没有方框、倒置、遮挡，以及点击继续是否正常。完整说明见 [安装及还原说明](docs/preview-install.txt)。

### 6. 不想继续测试时，怎样还原

退出游戏，把第 5 步保存的原版 `resources.assets` 复制回游戏的 `Ignorance_Data`，替换测试文件即可。

## 遇到问题怎么办

| 看到的情况 | 接下来怎么做 |
| --- | --- |
| 打开的是旧地址或旧页面 | 使用上面的仓库首页链接，确认分支为 `main`，然后刷新页面。 |
| 找不到 `requirements.txt` 或 `tools/build_preview.py` | 命令窗口位置不对；进入同时包含这两个文件的解压目录，重新打开 PowerShell。 |
| 提示找不到 `py` 或 Python 3.12 | 安装第 2 步指定的版本和启动器，然后重新打开 PowerShell。 |
| 依赖安装出现红色报错或 `No matching distribution found` | 先停止，把报错末尾完整复制反馈；Windows 依赖安装尚未实机验证。 |
| `Unsupported source build or already modified resources.assets` | 文件版本不同，或已装过测试包。用自己的原版备份构建，命令见下方；不要把补丁文件当原版输入。 |
| `Output already exists` | 已有输出不会被覆盖。确认已有 ZIP，或给构建命令加上 `--output build/preview-0.1-rebuild`，使用新的输出目录。 |
| 字体下载失败或 `Font checksum mismatch` | 先停止并反馈错误；不要跳过校验。 |
| `The rebuilt resource differs` | 此环境生成的资源与校验小样不一致，脚本不会生成 ZIP。先反馈错误，不要手动安装中间产物。 |
| 游戏中文字异常、卡住或无法启动 | 先退出并恢复原版备份，再反馈现象。 |

如果游戏目录中的文件已经被替换，可以从原版备份构建。下面路径只是例子，请换成自己的备份位置：

```powershell
.\.venv\Scripts\python.exe tools/build_preview.py --resources "E:\备份\resources.assets"
```

## 已验证与尚未验证的范围

资源回填、对象引用、字库覆盖和贴图重新读取已在 Linux/Python 3.12 中验证。构建脚本检查生成资源是否与已有小样逐字节一致；**尚未完成 Windows 构建及游戏内显示、换行、交互验证**。原始 ZIP 的完整性记录见 [交付校验记录](docs/delivery-verification.json)。新 ZIP 使用固定元数据，ZIP 哈希可能与原压缩包不同，内部游戏资源哈希必须相同。

输入原版 `resources.assets` 必须匹配本次测试的版本，SHA-256 为：

```text
1bc553fdc10358d2a4f78de1e2079a61ee46dc993636403dcfbc7b052b607b78
```

Linux 使用同一个入口：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build_preview.py --resources /path/to/original/resources.assets
```

## 文件说明

- `translations/preview.zh-CN.json`：14 条中文译文、稳定编号和原文校验值。
- `tools/build_preview.py`：从本地原版资源生成现有小样的完整入口。
- `tools/orwell_resources.py`：已验证的三类文本提取和回填工具。
- `tools/build_preview_font.py`：生成小样使用的静态 TextMesh Pro 中文备用字库。
- `tools/inspect_assembly.py`：静态读取托管程序集元数据，不运行游戏 DLL。
- `licenses/Noto-OFL.txt`：所用开放字体的 SIL OFL 1.1 许可。

`build/` 中的文件包含从本地游戏生成的资源，仅用于本地安装测试。请保持 `.gitignore` 中的游戏资源、字体缓存和输出目录排除规则，不将它们提交到仓库或发布为公开附件。

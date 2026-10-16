# Orwell: Ignorance is Strength 中文汉化项目

仓库：**[quellah1010-code/Orwell-Ignorance-is-Strength](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength)**。原名 `Orswell-ingnorance` 已重定向到此处。

目标是全游戏汉化。**目前交付 0.2 界面测试版，尚未完成全游戏翻译。**

本次加入欢迎页、创建档案流程、档案选项和设置页：130 处场景文字、38 条动态文字，包括“欢迎”“你已获准加入‘奥威尔’”“请创建个人档案”“空白档案”“创建”。保留上一版 14 条开场介绍及早期任务译文，中文字库扩展为 506 个字符。

制作人员名单正文、能力测试、网页、邮件和绝大多数剧情尚未完整翻译。游戏标识 ORWELL 保留，副标题译为“无知即力量”。**Windows 游戏内显示、换行和交互仍需实际测试。**

仓库仅保存源码、中文映射和构建说明。原版 DLL、assets、场景、原文全集及生成的补丁 ZIP 均不入库。使用你电脑上的原版文件生成本地测试包。

## 已经用过 0.1：这样升级到 0.2

1. [下载 main 分支源码 ZIP](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/archive/refs/heads/main.zip)，先“全部提取”到新文件夹。
2. 打开解压内容，找到 `README.md`、`tools`、`translations`、`docs` 所在那一层。将这一层的所有内容复制到你原来的工具文件夹，例如 `Orwell-Ignorance-is-Strength-work`，同意替换。保留原来的 `.venv`、`.cache` 和原版备份，不需要重装依赖。
3. 完全退出游戏。如果已安装旧测试包，先用当时保存的**原版 `resources.assets`** 恢复游戏文件；或在构建命令中用 `--resources` 指定原版备份。不要把旧补丁文件作为原版输入。
4. 在原工具文件夹的资源管理器地址栏输入 `powershell` 并回车，运行：

```powershell
.\.venv\Scripts\python.exe tools/build_menu.py --game-dir "E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength"
```

游戏路径已按你的截图填写；若移动过游戏，请修改引号内的路径。成功后显示 `Local ZIP:`，安装包位于：

```text
build\menu-0.2\orwell-zh-menu-0.2.zip
```

若直接使用原版备份，命令如下（将备份路径换成自己的）：

```powershell
.\.venv\Scripts\python.exe tools/build_menu.py --game-dir "E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength" --resources "C:\你的备份文件夹\resources.assets"
```

如已存在 `build/menu-0.2`，在命令末尾加上 `--output build/menu-0.2-retry`，使用一个新目录。成功构建不代表已在 Windows 游戏内验证。

## 第一次使用：安装 Python 和依赖

不需要安装 Git，也不需要操作 PR 或云环境。

1. [下载 main 源码 ZIP](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/archive/refs/heads/main.zip)，右键“全部提取”。打开能同时看到 `README.md`、`requirements.txt` 和 `tools` 的文件夹。
2. 打开 [Python 3.12.10 官方下载页](https://www.python.org/downloads/release/python-31210/)，在 Files 中下载 **Windows installer (64-bit)**。安装时勾选 **Add python.exe to PATH**，保留 Python Launcher（`py` 启动器），点击 Install Now。
3. 在工具文件夹的资源管理器地址栏输入 `powershell`，按回车，不需要管理员权限。
4. 逐条运行以下命令，每条结束后再运行下一条；遇到报错先停下：

```powershell
py -3.12 --version
```

应显示 `Python 3.12.x`。然后运行：

```powershell
py -3.12 -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```powershell
.\.venv\Scripts\python.exe tools/build_menu.py --game-dir "E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength"
```

安装依赖和首次下载开放字体需要联网。脚本校验输入文件和字体版本，只读取游戏目录，不会自动安装或替换游戏文件。

## 安装 0.2：备份和替换三个文件

**0.2 会修改资源、主菜单场景和程序集中的界面文字。必须备份下面三个原版文件。**

1. 完全退出游戏。在 Steam 游戏库中右键游戏 →“管理”→“浏览本地文件”。
2. 将以下文件复制到游戏目录外的备份文件夹，保留对应的文件名和目录结构。若装过 0.1，`resources.assets` 要使用安装 0.1 前保存的原版备份。

```text
Ignorance_Data/resources.assets
Ignorance_Data/level1
Ignorance_Data/Managed/Assembly-CSharp.dll
```

3. 解压生成的 `orwell-zh-menu-0.2.zip`，进入其中的 `orwell-zh-menu-0.2` 文件夹。
4. 将包内 `Ignorance_Data` 中的三个文件复制到游戏对应位置，同意替换。不要删除整个 `Managed` 或 `Ignorance_Data` 文件夹，也不要复制 `text-only-internal.assets` 等中间文件。
5. 启动游戏，保持英文语言设置。未创建档案时应看到中文欢迎页、“空白档案”和“创建”；已有存档时首页可能不同，自己的档案名称不会被改写。
6. 查看设置页，进入创建档案流程，检查中文、换行、头像和姓名输入、按钮点击及取消返回。长条款和隐私说明也需要检查是否遮挡。不要为了测试删除已有存档。

完整说明见 [0.2 安装与还原说明](docs/menu-install.txt)。

## 怎样还原

退出游戏，将备份的 **`resources.assets`、`level1`、`Managed/Assembly-CSharp.dll` 三个原版文件** 全部复制回对应位置。

只还原 `resources.assets` 会留下另外两处修改，不能算完整卸载。

## 常见问题

| 情况 | 操作 |
| --- | --- |
| 找不到 `build_menu.py` | 将新的 `tools` 文件夹完整复制到原来的工具文件夹。 |
| 找不到 `requirements.txt` | 在包含该文件的解压目录重新打开 PowerShell。 |
| `py` 或 Python 3.12 不存在 | 安装上面指定的版本及启动器，重新打开 PowerShell。 |
| `Unsupported source build or already modified resources.assets` | 原版资源不匹配或仍装着旧补丁。恢复原版，或使用 `--resources` 指定原版备份。 |
| `level1` 或 `Assembly-CSharp.dll` 版本不匹配 | 使用本次 Steam 版本的原版文件；已装 0.2 时先还原这两个文件才能重建。不要跳过校验。 |
| `Output already exists` | 命令末尾加上 `--output build/menu-0.2-retry`，使用尚不存在的目录。 |
| 字体下载失败、依赖安装失败 | 先停止，将报错末尾完整反馈。 |
| 运行的还是 `build_preview.py` | 那是旧 0.1 工具，只处理 14 条对白。当前界面版请用 `build_menu.py`。 |
| 游戏仍是英文或中文变方框 | 检查是否使用 0.2 ZIP、三个文件是否均替换到正确游戏目录；反馈截图。 |
| 游戏异常或无法启动 | 退出并恢复三个原版文件，再反馈问题。 |

## 已验证范围

- Linux / Python 3.12 完整构建成功，ZIP 的 CRC 和三份打包文件的 SHA-256 校验通过。
- 130 个场景对象按完整字段结构回读，只有文字字段变化；其他对象和外部引用保持不变。
- 38 条动态文字仅修改程序集用户字符串区的选定条目，保留全部方法代码和引用位置。检查了 10,942 个方法中的 2,952 次字符串引用。
- 原有 14 条译文、字体引用及字形贴图编码回读通过。字库明确使用 BASIC 排版引擎，避免旧版默认引擎不同造成的差异。
- 错误输入、被改坏的占位符和超过原槽位容量的程序集译文会被拒绝。
- **尚未完成 0.2 的 Windows 打包及游戏内渲染、换行和交互验证。** 资源结构检查不能替代这些测试。

见 [0.2 校验记录](docs/menu-verification.json)和[旧版校验记录](docs/delivery-verification.json)。

## 源码和映射

- `tools/build_menu.py`：当前 0.2 构建入口。
- `tools/menu_patch.py`：场景文字及程序动态文字回填和校验。
- `translations/menu.zh-CN.json`：130 处场景译文、38 条动态译文，以及编号和原文哈希；不包含原文列。
- `translations/preview.zh-CN.json`：保留的 14 条对白与任务译文。
- `tools/build_preview_font.py`：生成中文备用字库。
- `tools/build_preview.py`：旧 0.1 构建入口，保留供排查问题。
- `tools/orwell_resources.py`、`tools/inspect_assembly.py`：资源提取、回填和静态分析工具。
- `licenses/Noto-OFL.txt`：Noto CJK 开放字体许可。

生成的 `build/`、字体缓存、上传的游戏文件都不应提交到 GitHub 或公开发布。`.gitignore` 已排除这些文件，不要移除相应规则。

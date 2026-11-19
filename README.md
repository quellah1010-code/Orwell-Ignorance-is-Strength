# 《奥威尔》第二季中文测试版 · Windows 安装说明

这一版调大了「任务 1」和「任务 3」的选项文字，也改了拖拽时的高亮。**已经下载并解压工具的人，直接从第 2 步开始。**

### 1. 下载工具，点「全部解压」

[点这里下载汉化工具（ZIP）](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/archive/refs/heads/aptitude-layout-download.zip)

在 Windows 的「下载」文件夹找到它，右键点 **全部解压**。打开解压出来的文件夹，直到看见 **双击生成测试包.cmd**。如果你的电脑隐藏了扩展名，它会显示为「双击生成测试包」。

### 2. 双击「双击生成测试包」，选择原版游戏

先退出游戏。双击脚本后，会弹出「选择原版游戏目录」窗口。

- **已经装过旧汉化，而且留了原版备份**：选备份里那个叫 `Ignorance_Data` 的文件夹。里面应该有 `resources.assets`、`level1`、`level4`，以及 `Managed` 文件夹里的 `Assembly-CSharp.dll`。
- **游戏还是原版**：直接选 Steam 游戏目录，例如 `E:\SteamLibrary\steamapps\common\Orwell Ignorance is Strength`。找不到时，在 Steam 库里右键游戏，点「管理」→「浏览本地文件」。
- **装过旧汉化，又找不到原版备份**：先在 Steam 里右键游戏，点「属性」→「已安装文件」→「验证游戏文件的完整性」。等 Steam 恢复原版，再选游戏目录。

点「确定」后，等黑色窗口跑完。第一次运行需要联网。成功时会自动弹出文件夹，帮你选中 **orwell-zh-menu-0.3.zip**。这个 ZIP 就是要装进游戏的汉化包。

### 3. 备份，然后安装

1. 如果你已经存好了上面四个原版文件，可以直接往下做。否则先把游戏里的 `Ignorance_Data` 文件夹复制到游戏目录以外，留作备份。
2. 对刚生成的 **orwell-zh-menu-0.3.zip** 点「全部解压」。打开里面的 `orwell-zh-menu-0.3` 文件夹，复制其中的 **Ignorance_Data** 文件夹。
3. 打开 Steam 游戏目录。**看见原有的 Ignorance_Data 就在这里粘贴**，遇到同名文件选「替换」。这样四个新文件会进入各自的位置。
4. 启动游戏，语言保持 **English（英语）**。进入「任务 1」，把鼠标移到最后一项「我是为了钱。」上，看看底色是否跟着这行字，再试着拖到左边。Windows 实机的显示和拖拽还需要验证。

**想恢复原版？** 退出游戏，把备份的四个文件按原位置放回去，或者用 Steam 的「验证游戏文件的完整性」恢复。

### 如果卡住了

- **提示找不到 Python 或 py**：安装 Python 3.12 的「Windows installer (64-bit)」，安装时保留 Python Launcher，再双击脚本。[Python 官方下载页](https://www.python.org/downloads/release/python-31210/)
- **提示缺少文件、版本不符或 already modified**：回到第 2 步，选择原版备份或 Steam 恢复后的游戏目录。
- **其他错误**：把黑色窗口最后几行截个图，里面会显示卡在哪一步。

本包只覆盖部分界面和开场内容。需要查文件清单、字体许可或原版 0.3 的构建命令时，可看[原版 0.3 技术说明](https://github.com/quellah1010-code/Orwell-Ignorance-is-Strength/blob/737e52a90b7b833bf153f7ce6318be57475fa0d9/README.md)。

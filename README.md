# 长视频按要求修改成片 Skill

输入一条长视频、你要改变的一个或多个点，以及相关素材。Codex 先锁定改动范围与保留项，只处理受影响的镜头或音轨，验收后交付完整 MP4。改动可涉及人物、声音、场景、产品、文案、字幕或音乐，也可只改其中一项。需要生成画面时默认使用火山方舟 Seedance 2.0、720p；用户当次要求优先。

**[下载完整 Skill ZIP](https://github.com/Aiintalk/long-video-remake-skill/releases/latest/download/long-video-remake.skill.zip)** · [备用直链](https://raw.githubusercontent.com/Aiintalk/long-video-remake-skill/main/downloads/long-video-remake.skill.zip) · [查看 Skill 指令](skills/long-video-remake/SKILL.md)

## 安装

1. 下载 ZIP，解压得到 `long-video-remake` 文件夹，放入 `~/.codex/skills/`；Windows 放入 `%USERPROFILE%\.codex\skills\`。
2. 重新打开 Codex，在该 Skill 文件夹运行 `python3 scripts/setup.py`；Windows 用 `python`。脚本在用户目录创建独立环境，安装视频工具依赖。
3. 需要 Seedance 生成或素材库时，运行 `python3 scripts/run.py configure --all`，在本机隐藏输入自己的火山方舟 API Key、Access Key ID 和 Secret Access Key。Windows 将 `python3` 换成 `python`。只做本地字幕、音轨等修改可跳过密钥配置；密钥不在仓库或 ZIP 中。
4. 在 Codex 中说：`使用 $long-video-remake，只修改这条长视频中我指定的内容，其余保持原样，最后给我完整 MP4。`

只需安装这一份 Skill，不依赖其他 Skill。操作细节见[运行指南](skills/long-video-remake/references/usage.md)。

## 流程

长视频＋改动点＋所需素材 → 锁定修改范围与保留项 → 镜头切点与分段 → 选择复用、换音轨或生成 → 只制作受影响部分 → 质检 → 验证完整 MP4。

Skill 内含项目清单、短段切片、镜头切点辅助、方舟客户端、虚拟人像素材库操作、可续跑生成回执和 FFmpeg 拼接工具。默认复用原片；只有画面变化才提交相应生成任务。原音乐若与人声混在一起，替换音乐需要干净人声或新的完整混音，不能直接叠加两首音乐。所有结果按实际画面和声音验收。

使用者需要自己的方舟模型与项目权限、额度。私域虚拟人像库需要相应 AK/SK；上传本地素材还需自己的北京 TOS 存储桶及权限。API Key 本身不会自动开通这些权限。项目与发布包不包含任何密钥或个人素材。

# 长视频自动翻制成片 Skill

输入一条长视频、整片修改要求及人物、声音、产品等素材，让 Codex 按镜头分段制作，验收后拼接成完整 MP4。适合整体换人、换声音、换场景或改口播。默认火山方舟 Seedance 2.0、720p；用户当次要求优先。

**[下载完整 Skill ZIP](https://github.com/Aiintalk/long-video-remake-skill/releases/latest/download/long-video-remake.skill.zip)** · [备用直链](https://raw.githubusercontent.com/Aiintalk/long-video-remake-skill/main/downloads/long-video-remake.skill.zip) · [查看 Skill 指令](skills/long-video-remake/SKILL.md)

## 安装

1. 下载 ZIP，解压得到 `long-video-remake` 文件夹，放入 `~/.codex/skills/`；Windows 放入 `%USERPROFILE%\.codex\skills\`。
2. 重新打开 Codex，在该 Skill 文件夹运行 `python3 scripts/setup.py`；Windows 用 `python`。脚本在用户目录创建独立环境，安装视频工具依赖。
3. 运行 `python3 scripts/run.py configure --all`，在本机隐藏输入自己的火山方舟 API Key、Access Key ID 和 Secret Access Key。Windows 将 `python3` 换成 `python`。密钥保存在系统凭据库，不在仓库或 ZIP 中。
4. 在 Codex 中说：`使用 $long-video-remake，根据这条长视频、我的修改要求和人物/声音/产品素材，直接生成完整 MP4。`

只需安装这一份 Skill，不依赖其他 Skill。操作细节见[运行指南](skills/long-video-remake/references/usage.md)。

## 流程

长视频＋修改要求＋素材 → 检查输入 → 镜头切点与分段 → 固定人物/声音/产品参考 → 逐段生成 → 逐段验收 → 拼接字幕音乐 → 验证完整 MP4。

Skill 内含项目清单、短段切片、镜头切点辅助、方舟客户端、虚拟人像素材库操作、可续跑生成回执和 FFmpeg 拼接工具。长片按官方单次时长限制拆成短段；不合格片段局部重做。实际人物、音色、逐字台词和口型需要检查生成结果。

使用者需要自己的方舟模型与项目权限、额度。私域虚拟人像库需要相应 AK/SK；上传本地素材还需自己的北京 TOS 存储桶及权限。API Key 本身不会自动开通这些权限。项目与发布包不包含任何密钥或个人素材。

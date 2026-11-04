# 运行指南

命令均在本 Skill 目录执行。需要 Python 3；只有提交视频生成或使用素材库时才需要网络与火山方舟权限。本地素材上传私域虚拟人像库还需使用者自己的北京 TOS 桶与相应权限。Windows 将 `python3` 换成 `python`。

## 首次安装

1. `python3 scripts/setup.py`：在用户目录的 `.long-video-remake/venv` 建立独立环境，安装 `keyring`、`tos` 和 FFmpeg 执行器。
2. 需要视频生成或素材库时，运行 `python3 scripts/run.py configure --all`，通过本机隐藏输入配置 API Key、Access Key ID、Secret Access Key；也支持临时环境变量 `ARK_API_KEY`、`VOLC_ACCESS_KEY_ID`、`VOLC_SECRET_ACCESS_KEY`。只做本地剪辑可跳过。
3. `python3 scripts/run.py status`：只显示是否存在，不输出密钥。

生成接口、素材库与 TOS 是不同权限。只使用公网 HTTPS 参考素材时，视频生成需要 API Key；使用私域虚拟人像库需要同项目 AK/SK；上传本地素材还需要 TOS 桶。配置密钥不等于获得这些权限。

## 建立项目

```bash
python3 scripts/run.py project inspect /path/input.mp4
python3 scripts/run.py project cuts /path/input.mp4 --output /path/cuts.json
python3 scripts/run.py project init --input /path/input.mp4 --output /path/project --cuts /path/cuts.json --resolution 720p --ratio 9:16
```

`cuts` 用快速采样给出候选镜头切点，需结合人声和实际画面复核。`init` 自动切成约 10 秒、每段不超过 15 秒的参考片，优先贴近切点，并生成 `manifest.json`。也可手写秒数 JSON 作为切点文件，或不提供 `--cuts`。初始化后按实际镜头、说话停顿复核分段；不适合的切点在提交生成前重建项目或调整对应短段。

`init` 默认把所有段标记为 `reuse`。按[项目清单](manifest.md)填“改动点、作用范围、保留项”；只将受影响段改为 `generate` 或 `replace_audio`。`replace_audio` 段填写 `replacement_audio` 本地路径；可见口播变动应通过生成画面或有口型同步的处理方式完成。需生成的段填写 `specs/S001-v1.json` 等 spec 文件。下面是“只改背景”的示例：

```json
{
  "prompt": "参考视频1的镜头节奏与人物动作，仅把原背景换成浅米色咨询间。人物身份、服装、产品、台词、音色、语速和手势顺序保持参考视频一致。",
  "duration": 10,
  "resolution": "720p",
  "ratio": "9:16",
  "project": "default",
  "generate_audio": true,
  "references": [
    {"type": "video", "url": "https://example.com/authorized-reference-segment.mp4"}
  ]
}
```

这些 URL 和 ID 只是格式示例，必须替换为实际可访问、已核准的素材。`duration` 是 4–15 秒整数；细分时长、参考素材数量和格式按当前官方接口检查。每段的来源参考视频不得超限。`project` 用于私域资产核对，API Key 本身也须属于同项目。

若要求**换人物、原动作与时间完全对齐**，逐段以原短片作为视频1，新人物图片或视频只提供身份。先在 `segments[].notes` 记录该段动作的相对时间锚点（起势、手势转折、停顿、视线、切点），再为该段写编辑提示词：

> 严格编辑视频1，只将原人物替换为图片1中的新人物。图片1只定义新人物的外观；视频1是唯一动作和时间轴来源。0.0–1.5秒：[实际动作A]；1.5–3.0秒：[实际动作B]；3.0–5.0秒：[实际动作C]。新人物在原时间点完成相同身体和手部轨迹、视线变化及停顿；原场景、道具、机位、构图、镜头切点和总时长保持一致。不得增加、删除、重排动作或改变动作速度；不得继承原人物的脸和外观。

若用新人物视频，则按请求体顺序改为“视频2中的新人物”，明确视频2只提供身份、不能提供动作。示意秒数必须换成原段实际时间码。台词同时变化时，只放开嘴唇以匹配新台词，身体动作仍按原段。生成后把原段与候选段按相同时间码并排检查；动作时机有偏移的候选片段不能 `project accept`。提示词本身不能保证逐帧完全一致。

## 素材接入

```bash
python3 scripts/run.py groups --project default
python3 scripts/run.py assets --project default --group-id group-...
python3 scripts/run.py asset-create --group-id group-... --type Image --url https://example.com/person.png --project default
python3 scripts/run.py asset-create --group-id group-... --type Video --file /path/segment.mp4 --bucket YOUR_BUCKET --project default
python3 scripts/run.py asset-wait asset-... --project default
```

本地上传经使用者已有的 TOS 桶；素材状态为 `Active` 后才能用 `asset://`。视频、图、音频参考都必须通过实际接口参数提交。临时签名 URL 不应写入公开项目或聊天。

## 生成、验收、成片

```bash
python3 scripts/run.py project batch --manifest /path/project/manifest.json
python3 scripts/run.py project batch --manifest /path/project/manifest.json --segment S001 --submit
python3 scripts/run.py project batch --manifest /path/project/manifest.json --submit
python3 scripts/run.py project accept --manifest /path/project/manifest.json --segment S001
python3 scripts/run.py project assemble --manifest /path/project/manifest.json
python3 scripts/run.py project verify /path/project/final.mp4
```

未加 `--submit` 只做本地预检，显示待生成段数和总生成秒数。没有 `generate` 段时，跳过这两条批量生成命令。先用 `--segment` 提交并验收一段高风险镜头，再做余下片段。提交后保存 `specs/*.receipt.json`；如中断，原命令可从已有任务回执继续查询。`accept` 只表示操作者已看、已听并同意使用候选段，脚本本身不会判断人物或口型。所有待生成段验收完毕才允许 `assemble`。

`manifest.json` 的 `music` 可指向本地音频，拼接时按 `music_volume` 混入；`subtitles` 可指向按最终人声制作的 SRT。字幕烧录依赖 FFmpeg 的 `subtitles` 滤镜。`music` 是叠加，不会移除原音轨里的音乐；若要替换已与人声混合的原音乐，先准备干净的人声或新的完整混音，再给受影响段设置 `replace_audio` 和 `replacement_audio`。如果原段只有背景音乐，可把该段 `audio_policy` 设为 `mute` 后叠加新音乐；含人声的段不能这样做。

## 官方文档

- [Seedance 2.0 专属能力](https://docs.volcengine.com/docs/ark/seedance-2-0?lang=zh)
- [创建视频生成任务](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
- [肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh)
- [私域虚拟人像库](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview?lang=zh)

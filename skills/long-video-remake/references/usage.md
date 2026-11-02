# 运行指南

命令均在本 Skill 目录执行。需要 Python 3、网络、火山方舟视频生成权限；本地素材上传私域虚拟人像库还需使用者自己的北京 TOS 桶与相应权限。Windows 将 `python3` 换成 `python`。

## 首次安装

1. `python3 scripts/setup.py`：在用户目录的 `.long-video-remake/venv` 建立独立环境，安装 `keyring`、`tos` 和 FFmpeg 执行器。
2. `python3 scripts/run.py configure --all`：通过本机隐藏输入配置 API Key、Access Key ID、Secret Access Key；也支持临时环境变量 `ARK_API_KEY`、`VOLC_ACCESS_KEY_ID`、`VOLC_SECRET_ACCESS_KEY`。
3. `python3 scripts/run.py status`：只显示是否存在，不输出密钥。

生成接口、素材库与 TOS 是不同权限。只使用公网 HTTPS 参考素材时，视频生成需要 API Key；使用私域虚拟人像库需要同项目 AK/SK；上传本地素材还需要 TOS 桶。配置密钥不等于获得这些权限。

## 建立项目

```bash
python3 scripts/run.py project inspect /path/input.mp4
python3 scripts/run.py project cuts /path/input.mp4 --output /path/cuts.json
python3 scripts/run.py project init --input /path/input.mp4 --output /path/project --cuts /path/cuts.json --resolution 720p --ratio 9:16
```

`cuts` 用快速采样给出候选镜头切点，需结合人声和实际画面复核。`init` 自动切成约 10 秒、每段不超过 15 秒的参考片，优先贴近切点，并生成 `manifest.json`。也可手写秒数 JSON 作为切点文件，或不提供 `--cuts`。初始化后按实际镜头、说话停顿复核分段；不适合的切点在提交生成前重建项目或调整对应短段。

按[项目清单](manifest.md)填人物、声音、素材和每段操作。需生成的段填写 `specs/S001-v1.json` 等 spec 文件。每个 spec 遵循内置客户端格式，例如：

```json
{
  "prompt": "视频1提供手势与机位节奏。图片1中的目标人物在相同空间位置完成手势，脸、发型和服装保持一致。准确说出：示例台词。音频1只用于目标音色和语速。嘴型对应每个字；不要继承视频1中的旧人脸、旧声音或旧背景。",
  "duration": 10,
  "resolution": "720p",
  "ratio": "9:16",
  "project": "default",
  "generate_audio": true,
  "references": [
    {"type": "video", "url": "https://example.com/reference-segment.mp4"},
    {"type": "image", "url": "asset://asset-EXAMPLE"},
    {"type": "audio", "url": "https://example.com/target-voice.mp3"}
  ]
}
```

这些 URL 和 ID 只是格式示例，必须替换为实际可访问、已核准的素材。`duration` 是 4–15 秒整数；细分时长、参考素材数量和格式按当前官方接口检查。每段的来源参考视频不得超限。`project` 用于私域资产核对，API Key 本身也须属于同项目。

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

未加 `--submit` 只做本地预检，显示待生成段数和总生成秒数。先用 `--segment` 提交并验收一段高风险镜头；再对余下片段运行整片命令。提交后保存 `specs/*.receipt.json`；如中断，原命令可从已有任务回执继续查询。`accept` 只表示操作者已看、已听并同意使用候选段，脚本本身不会判断人物或口型。所有待生成段验收完毕才允许 `assemble`。

`manifest.json` 的 `music` 可指向本地音频，拼接时以低于人声的音量混入；`subtitles` 可指向按最终人声制作的 SRT。字幕烧录依赖 FFmpeg 的 `subtitles` 滤镜，使用前核对当前安装版本是否支持。

## 官方文档

- [Seedance 2.0 专属能力](https://docs.volcengine.com/docs/ark/seedance-2-0?lang=zh)
- [创建视频生成任务](https://docs.volcengine.com/docs/ark/create-video-generation-task-api?lang=zh)
- [肖像素材指南](https://docs.volcengine.com/docs/ark/seedance-portrait-asset-guide?lang=zh)
- [私域虚拟人像库](https://docs.volcengine.com/docs/ark/private-virtual-avatar-library-guide-preview?lang=zh)

# 项目清单

`project init` 生成 `manifest.json`、`refs/`、`specs/`、`candidates/`、`work/`。清单是续跑与成片的唯一顺序来源；不要把密钥、临时签名 URL 或用户隐私素材内容复制进去。

| 字段 | 用途 |
| --- | --- |
| `source` | 原片绝对路径及检查到的时长、画幅、帧率、音轨 |
| `model`, `resolution`, `ratio`, `project_name` | 全片生成与导出规格，默认 Seedance 2.0、720p |
| `global_requirements` | 整片统一换人、换声、保留与替换项；由代理在生成前补齐 |
| `segments[]` | 按时间码排序的短段；每段有稳定 `id`、`source_start/end` 和 `source_clip` |
| `segments[].operation` | `generate` 重做该段；`reuse` 原片复用 |
| `segments[].source_ref_url` | 若用原片动作作参考，记录已上传的该短段 HTTPS 或 `asset://` 地址 |
| `segments[].spec` | 该段的 Seedance 请求 JSON，相对项目目录或绝对路径；更新提示词用新版本文件名 |
| `segments[].candidate_video` | 已生成、待验收片段，由工具填写 |
| `segments[].accepted_video` | 看听验收后采纳的视频，由 `project accept` 填写 |
| `segments[].dialogue`, `notes` | 最终应说台词、动作/连续性和质检记录 |
| `music`, `subtitles` | 可选音频文件和 SRT 路径 |
| `final_video` | 完整 MP4，由 `project assemble` 填写 |

`global_requirements` 应写清替换范围，例如整片出现旧人物的所有段、新人物统一形象、目标音色、产品画面是否保留、口播逐字稿和目标音乐。逐段 spec 必须与这些要求一致。参考视频中含真实人脸时，先按当前方舟肖像素材规则确定可用的输入路径。

输出影片的字幕以**实际生成的人声**为准。字幕文件和音乐可以在生成后加入清单，再重新导出；修改某段口播或人像时，只重做该段并重新拼接。

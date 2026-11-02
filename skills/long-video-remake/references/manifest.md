# 项目清单

`project init` 生成 `manifest.json`、`refs/`、`specs/`、`candidates/`、`work/`。清单是续跑与成片的唯一顺序来源；不要把密钥、临时签名 URL 或用户隐私素材内容复制进去。

| 字段 | 用途 |
| --- | --- |
| `source` | 原片绝对路径及检查到的时长、画幅、帧率、音轨 |
| `model`, `resolution`, `ratio`, `project_name` | 全片生成与导出规格，默认 Seedance 2.0、720p |
| `global_requirements.changes` | 用户指定的一个或多个改动点、作用范围及目标结果 |
| `global_requirements.preserve` | 用户明确要求保持的内容；未提到的属性也默认保留 |
| `global_requirements.asset_anchors` | 需要跨段统一的新素材及其用途 |
| `global_requirements.forbidden_inheritance` | 不能从参考片继承的旧属性 |
| `segments[]` | 按时间码排序的短段；每段有稳定 `id`、`source_start/end` 和 `source_clip` |
| `segments[].operation` | `reuse` 原片复用，`replace_audio` 保留画面并换完整音轨，`generate` 生成变化画面；默认 `reuse` |
| `segments[].changes`, `preserve` | 该段要改和要保留的具体属性 |
| `segments[].replacement_audio` | `replace_audio` 段使用的本地完整音频文件，时长不可超出画面 |
| `segments[].audio_policy` | `keep` 保留该段原声音；`mute` 将该段原声音静音。静音会同时移除原人声 |
| `segments[].source_ref_url` | 若用原片动作作参考，记录已上传的该短段 HTTPS 或 `asset://` 地址 |
| `segments[].spec` | 该段的 Seedance 请求 JSON，相对项目目录或绝对路径；更新提示词用新版本文件名 |
| `segments[].candidate_video` | 已生成、待验收片段，由工具填写 |
| `segments[].accepted_video` | 看听验收后采纳的视频，由 `project accept` 填写 |
| `segments[].dialogue`, `notes` | 最终应说台词、动作/连续性和质检记录 |
| `music`, `music_volume`, `subtitles` | 可选背景音乐、其混音音量（默认 0.12）和 SRT 路径 |
| `final_video` | 完整 MP4，由 `project assemble` 填写 |

`global_requirements` 应写清改动范围和保留范围。例如只改背景音乐，就不要自动改人物、口播或产品；整体换产品则需覆盖产品出现的每一段，但其他画面尽量复用。逐段 spec 必须与这些要求一致。参考视频中含真实人脸时，先按当前方舟肖像素材规则确定可用的输入路径。

输出影片的字幕以**最终实际人声**为准。字幕文件和音乐可以在生成后加入清单，再重新导出。原背景音乐与人声若在同一音轨，`music` 只会叠加新音乐；要真正替换旧音乐，须先分离干净人声或提供新的完整音轨，再按段使用 `replace_audio`。修改某段画面或口播时，只重做该段并重新拼接。

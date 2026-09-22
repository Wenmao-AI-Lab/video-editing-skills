# 剪映草稿生成 · 内部说明（AI灵匣）

## 这条线解决什么问题
视频剪辑包"全流程"之前断在：01-07 出"人读方案"，08 出"机器成片"，中间缺接口。
08 桥接器把方案落成 `manifest.json`，ffmpeg 线吃完它直接渲染。但很多买家习惯用剪映精修/套模板，
于是本技能让**同一份 manifest.json** 也能变成剪映草稿——方案层产出在剪映里"自动铺好时间线"，不再手动拖素材。

## manifest.json → 剪映草稿 字段映射
| manifest 字段 | 剪映草稿落点 |
|---|---|
| `clips[]`（素材路径） | 视频轨：按 ffmpeg 探测的真实时长顺序排布 |
| `resolution.w/h` | 画布尺寸（ScriptFile width/height） |
| `fps` | 工程帧率 |
| `subtitle`（.srt 路径） | 字幕轨：经 `import_srt` 导入，与 ffmpeg 烧录同一份 |
| `title`（可选/命令行 --title） | 标题轨：一个加粗文字段 |
| `audio`（可选/命令行 --audio） | 音频轨：覆盖总时长 |
| `color_preset` | 仅记录，供买家在剪映一键套 07 类对应调色 LUT |

## 剪映草稿格式要点
- 剪映草稿是一个**文件夹**：`xxx.draft/draft_content.json`。
- `draft_content.json` 顶层含 `tracks`（视频/音频/文字…）、`materials`（videos/audios/texts…）、`canvas_config` 等。
- 本技能用 `pyJianYingDraft` 生成，已实测可产出合法工程（视频轨/字幕轨/标题轨/音频轨齐全）。

## 买家怎么用
1. 运行 `gen_jianying_draft.py` 得到 `xxx.draft/` 文件夹。
2. 把 `xxx.draft` 文件夹复制到剪映的「草稿」目录（或剪映内「草稿恢复/导入」）。
3. 打开剪映即见排好的时间线，点「导出」出片；需要精修/套模板就在剪映里直接改。

## 与 ffmpeg 线的关系
- 输入完全一致（同一个 manifest.json）→ 两条线可并行，买家二选一。
- ffmpeg 线：全自动、无界面、适合矩阵号日更。
- 剪映线：半自动、有界面、适合要精修/套剪映模板的买家。

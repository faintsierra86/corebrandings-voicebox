# Voicebox 维护版 0.6.0-local.1 修复清单

核对日期：2026-10-09。官方公开安装包仍为 0.5.0（2026-04-25）；官方源码已准备 0.6.0，尚未公开发布对应安装包。本维护版基于官方 0.6.0 准备提交 a00d271，加上 mlx-audio #914 的语速修复。

这是自建维护版本，不是官方发布。整合范围为官方 0.6.0 稳定性修复批次；后续未发布的新引擎、云服务、外部大模型和新导出功能不属于这批修复。未知或尚未修复的问题不能因为本次升级就视为解决。

## 与 M 系列 Mac 直接相关的修复

| 问题/变化 | 官方修复 | 本维护版 |
|---|---|---|
| Qwen 长语音逐渐加速 | [mlx-audio #914](https://github.com/Blaizzy/mlx-audio/pull/914) | 保留最近 64 个音频标记的重复惩罚；单条和批量采样均修复 |
| MLX 模型加载和生成跨线程，偶发 Stream(gpu, 1) 崩溃 | [#1154](https://github.com/jamiepine/voicebox/pull/1154) | TTS、Whisper、Qwen LLM 共用单工作线程，加载与推理在一次提交中 |
| 卸载模型后 GPU 内存未释放 | [#1161](https://github.com/jamiepine/voicebox/pull/1161) | 清提示缓存和 MLX 分配器，处理推理失败的引用及生成中卸载 |
| 连续生成导致内存持续增长 | [#1149](https://github.com/jamiepine/voicebox/pull/1149) | 每次生成及流式生成后清理缓存，清理失败不破坏已成功结果 |
| Qwen 生成不结束、尾部噪音拖长 | [#964](https://github.com/jamiepine/voicebox/pull/964) | 检测异常长输出，拆分重试；无法再拆分时保留裁剪片段 |
| 下载完成的模型离线时仍不断联网重试 | [#1130](https://github.com/jamiepine/voicebox/pull/1130) | 加载缓存完整模型时临时离线；缺关键文件时仍正常下载 |
| 加载 Qwen LLM 后把整个进程错误切成离线 | [#924](https://github.com/jamiepine/voicebox/pull/924) | 去掉全局离线状态污染 |
| 下载失败后仍显示下载中 | [#926](https://github.com/jamiepine/voicebox/pull/926)、[#1133](https://github.com/jamiepine/voicebox/pull/1133) | 下载状态过滤错误任务，识别遗留的不完整文件 |
| 前台关闭后日志管道断开，后台请求报错 | [#1141](https://github.com/jamiepine/voicebox/pull/1141) | 安全日志输出，处理 Broken pipe |
| SQLite 多任务时容易锁库 | [#1136](https://github.com/jamiepine/voicebox/pull/1136) | WAL 日志和 5 秒锁等待 |
| 历史记录、故事列表查询慢 | [#1139](https://github.com/jamiepine/voicebox/pull/1139)、[#1143](https://github.com/jamiepine/voicebox/pull/1143)、[#663](https://github.com/jamiepine/voicebox/pull/663) | 索引和批量查询 |
| 删除声音留下孤立记录或删除一半失败 | [#1148](https://github.com/jamiepine/voicebox/pull/1148) | 原子提交和文件锁处理；删除声音也会删除其生成记录，界面明确提示 |
| 指定模型加载/卸载时却总操作 Qwen | [#1138](https://github.com/jamiepine/voicebox/pull/1138) | 按实际请求的模型操作 |
| 未指定引擎时忽略声音自己的引擎配置 | [#1140](https://github.com/jamiepine/voicebox/pull/1140) | 使用声音配置 |
| 失败生成的音频返回服务器错误 | [#893](https://github.com/jamiepine/voicebox/pull/893) | 正常返回未找到 |
| 头像上传文件名缺失时报错 | [#954](https://github.com/jamiepine/voicebox/pull/954) | 校验文件名 |
| 关闭文字润色后，听写仍要求下载 LLM | [#1147](https://github.com/jamiepine/voicebox/pull/1147) | 只在开启润色时要求 LLM |
| 上传 WebM 等录音转写失败 | [#957](https://github.com/jamiepine/voicebox/pull/957)、[#903](https://github.com/jamiepine/voicebox/pull/903) | 保留扩展名并转换为 WAV |
| 听写不能粘贴到部分 Electron 应用 | [#952](https://github.com/jamiepine/voicebox/pull/952) | 修正 macOS Command 按键标志 |
| fn 键不能作为听写快捷键 | [#950](https://github.com/jamiepine/voicebox/pull/950) | 增加 fn 键支持 |
| 中文声音通过 speak/MCP 播放却默认英语 | [#1137](https://github.com/jamiepine/voicebox/pull/1137) | 按声音档案语言生成 |
| MCP 工具名称中的点被客户端拒绝 | [#1135](https://github.com/jamiepine/voicebox/pull/1135) | 改为 voicebox_speak 等下划线名字；旧配置需调整 |
| Kokoro 短稿尾部静音或杂音 | [#1150](https://github.com/jamiepine/voicebox/pull/1150) | 仅裁剪首尾，保留内部停顿 |
| Kokoro 列表缺少 4 个普通话男声 | [#788](https://github.com/jamiepine/voicebox/pull/788) | 补充列表 |
| Chatterbox 多语言在 Apple 芯片上走慢 CPU 路径 | [#1162](https://github.com/jamiepine/voicebox/pull/1162) | 新增 MLX 路径、缓存检查与异常长输出重试 |
| 长报错被截断，无法查看全文 | [#1134](https://github.com/jamiepine/voicebox/pull/1134) | 显示摘要并可复制原错误 |
| 底部生成框的模型/语言菜单被裁掉 | [#936](https://github.com/jamiepine/voicebox/pull/936) | 菜单向上展开 |
| 导出相同文稿时文件名重复 | [#956](https://github.com/jamiepine/voicebox/pull/956) | 文件名包含生成记录 ID |
| 时间显示偏差 | [#953](https://github.com/jamiepine/voicebox/pull/953)、[#1146](https://github.com/jamiepine/voicebox/pull/1146) | 统一 UTC 处理 |
| 前端 seroval 旧版本问题 | [#1132](https://github.com/jamiepine/voicebox/pull/1132) | 按官方锁文件固定 1.5.3 |

另外加入 [82caf7d](https://github.com/jamiepine/voicebox/commit/82caf7d) 的冻结程序启动兼容修复：等待 Torch 完全导入后再包装 from_numpy，并修正 NumPy 兼容回退中的变量名。

## 其他平台和引擎

0.6.0 源码中的 Windows、Linux、Docker、ROCm、PyTorch 长音频转写、TADA 等修复也在所选源码里。这个安装包仅用于 Apple 芯片的 macOS；这些路径没有在本机实测，不将它们列为验证通过。

## 构建和验证边界

前端和原生 macOS 程序从上述源码重新编译。Python 后台用同一源码整体替换；保留原 0.5.0 的 Python 3.12 与第三方运行库，仅对 Qwen 的重复惩罚加入已合并补丁。非后台 Python 模块和原生依赖的内容会做逐项比较。图标复用原程序已编译资源。新电脑无需安装 Python、Rust 或 Bun。

运行库的复用不是把所有第三方库升级到最新版；整包替换未经兼容验证的依赖会引入另外的问题。本次针对已确认修复做可复现整合。具体通过的检查以附带测试报告为准；尚未下载的其他语音模型不宣称已经做过真实合成测试。

来源：[官方 0.6.0 更新记录](https://github.com/jamiepine/voicebox/blob/a00d271/CHANGELOG.md)、[完整源码差异](https://github.com/jamiepine/voicebox/compare/v0.5.0...a00d271)、[官方公开发布列表](https://github.com/jamiepine/voicebox/releases)。

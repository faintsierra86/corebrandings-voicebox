# 维护源码和构建说明

基线：jamiepine/voicebox 的 a00d271（0.6.0 准备版本）。原官方公开运行库来自 0.5.0 Apple Silicon 包；构建脚本按 SHA256 检查输入，拒绝其他运行库。

1. 从社区仓库检出 corebrandings-preview 分支；或从源码附件解压 upstream-source.tar.gz 后应用本地维护改动.patch。
2. 保留原 Voicebox 0.5.0 在 /Applications/Voicebox.app。构建后台需要 Python 3.12，执行 build_backend.py，--repo 指向 voicebox-maintenance，--output 指向生成的 voicebox-server。
3. 用 Bun 1.3.8 执行锁文件安装，再编译 tauri 的前端；用 Rust 和 cargo --locked 构建原生主程序，启用 custom-protocol。MACOSX_DEPLOYMENT_TARGET=15.0。
4. 按官方约定将 voicebox-server 和未改动的 voicebox-mcp 放到 tauri/src-tauri/binaries 下，附带 aarch64-apple-darwin 后缀。
5. 没有完整版 Xcode 时，VOICEBOX_PREBUILT_ICON_DIR 指向原程序 Contents/Resources，复用已编译的同一图标。此次构建用本机已有 MacOSX26.5.sdk，通过 SDKROOT 指定，没有改变系统默认 SDK。
6. 用官方 app bundle 或 Tauri bundle 包装，设置维护版名称、版本、macOS 最低 15.0；用本地临时签名并严格验证，生成 DMG。

build_backend.py 保持 PyInstaller 外层 Mach-O 大小，重建整个后台和入口、NumPy 兼容 hook；对其他 Python 代码和原生库逐项检查内容不变。重新压缩 Python 模块腾出空间，仅改变压缩编码，不改变代码。第三方语音库仅添加 Qwen 重复惩罚窗口修复。

test_numpy_hook.py 验证实际打包 hook；语速检查脚本来自第一次修复。后台检查采用官方对应源码的回归测试。维护包的测试报告记录实际通过的项目。完整源码仍保留其原许可。

公司维护标识：正泽 · Corebrandings。公开源码仓库的脚本在 scripts/community 下；Python 3.12 执行 build_backend.py 时 --repo 指向仓库根目录，--original 可显式指定官方 0.5.0 未签名修改前的后台二进制。版本仍采用 0.6.0-local.1。Bun 和 Rust 只用于构建，不是用户安装依赖。社区预览版通过发布页手动更新。

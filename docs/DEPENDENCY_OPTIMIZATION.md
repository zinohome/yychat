# 依赖优化建议

## 当前警告分析

### 1. WebSocket 警告
- **问题**: `websockets.WebSocketServerProtocol` 已弃用
- **影响**: 功能正常，但未来版本可能不兼容
- **建议**: 升级到最新版本的 `websockets` 库

### 2. 正则表达式警告
- **问题**: `pydub` 库中的无效转义序列
- **影响**: 仅警告，不影响功能
- **建议**: 等待 `pydub` 库更新或使用替代方案

### 3. audioop 模块警告
- **问题**: `audioop` 模块将在 Python 3.13 中移除
- **影响**: 长期兼容性问题
- **建议**: 升级 `pydub` 到支持新音频处理方式的版本

## 优化方案

### 方案1: 依赖升级 (推荐)
```bash
# 升级到最新版本
pip install --upgrade websockets pydub webrtcvad

# 或者指定版本
pip install websockets>=12.0 pydub>=0.25.1 webrtcvad>=2.0.10
```

### 方案2: 警告抑制 (已实现)
- 已在 `utils/warning_suppression.py` 中实现
- 在 `app.py` 启动时自动应用
- 不影响功能，仅减少控制台输出

### 方案3: 静默启动 (立即可用)
```bash
# 使用静默启动脚本
cd yychat
python start_quiet.py

# 或使用 shell 脚本
./scripts/start_quiet.sh

# 或直接设置环境变量
PYTHONWARNINGS=ignore python app.py
```

### 方案4: 替代库 (长期)
考虑使用以下替代库：
- `websockets` → `fastapi-websocket` 或 `socketio`
- `pydub` → `librosa` 或 `soundfile`
- `webrtcvad` → `py-webrtcvad` 或自实现 VAD

## 实施建议

### 立即实施 (已完成)
- ✅ 添加警告抑制配置
- ✅ 优化日志级别
- ✅ 减少控制台噪音

### 短期优化 (1-2周)
- 升级 `websockets` 到最新版本
- 测试兼容性
- 更新相关代码

### 长期规划 (1-3个月)
- 评估替代音频处理库
- 实现更现代的 WebSocket 处理
- 减少对弃用模块的依赖

## 测试建议

升级后需要测试：
1. WebSocket 连接稳定性
2. 音频录制和播放功能
3. 实时语音对话功能
4. 错误处理和恢复机制

## 监控指标

- 警告数量减少
- 启动时间优化
- 内存使用稳定
- 功能完整性保持

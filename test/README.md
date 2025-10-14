# 测试文件说明

本目录包含yychat项目的各种测试文件，包括单元测试、集成测试和临时测试脚本。

## 目录结构

```
test/
├── unit/                    # 单元测试
├── integration/             # 集成测试
├── e2e/                     # 端到端测试
├── fixtures/                # 测试数据和固件
├── test_websocket.py        # WebSocket功能测试
├── test_voice_fixed.py      # 语音功能测试（修复版）
├── test_realtime_voice.py   # 实时语音对话测试
├── test_debug_voice.py      # 语音调试测试
├── test_simple_voice.py     # 简单语音测试
├── test_audio_api.py        # 音频API测试
├── test_speech.mp3          # 测试音频文件
└── README.md               # 本文件
```

## 临时测试脚本

### WebSocket功能测试
```bash
cd test
source ../.venv/bin/activate
python3 test_websocket.py
```

### 语音功能测试
```bash
cd test
source ../.venv/bin/activate
python3 test_voice_fixed.py
```

### 实时语音对话测试
```bash
cd test
source ../.venv/bin/activate
python3 test_realtime_voice.py
```

### 音频API测试
```bash
cd test
source ../.venv/bin/activate
python3 test_audio_api.py
```

## 运行前准备

1. 确保yychat服务器正在运行：
   ```bash
   cd ..  # 回到项目根目录
   source .venv/bin/activate
   python3 app.py
   ```

2. 激活虚拟环境：
   ```bash
   source ../.venv/bin/activate
   ```

## 注意事项

- 所有测试脚本都需要服务器运行在 `localhost:9800`
- 测试脚本会创建临时连接，测试完成后会自动断开
- 某些测试可能需要有效的API密钥配置
- 音频相关测试需要真实的音频文件格式

## 添加新的测试文件

当需要创建新的临时测试文件时，请：

1. 将文件放在 `test/` 目录下
2. 使用 `test_` 前缀命名
3. 在本文档中添加使用说明
4. 确保测试完成后清理资源

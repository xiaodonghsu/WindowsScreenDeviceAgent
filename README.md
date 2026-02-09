# 中控系统

## CMS -- strapi

完成内容管理: 屏幕-场景-资源(媒体)


## IOT -- ThingsBoard

完成设备接入功能--MQTT 接入； 状态管理

### 控制面板依托IOT



## Windows-Screen-Agent

### 工作流程

1. 开机
  - 使用固定的参数 -- cms_baseurl  -- devcice_name , 从 CMS 获取 IOT 的 Access-Token
  - 从 CMS 获取 config, 包含 IOT 连接信息, device_id, device_token,  保存为文件
  - MQTT 连接到 IOT
  - 查询 Attributes - sence 获取执行的场景名;
  - 获取到场景名, 自动从 CMS 以 device_name - scene 获取到 assets - 这是一个播放的内容列表
    - 场景一旦切换, 自动进入第一个节目, 如果是 video , 需要自动暂停

2. 待机
  - MQTT 监听, 等带指令下发

3. 接收到指令, 开始执行指令.


## 讲解员角色

## 打包

使用PyInstaller将脚本打包成可执行文件：

```bash
uv run pyinstaller -F main.py
```

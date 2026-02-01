[app]

# 应用名称
title = Schedule Manager

# 包名（只能用小写字母、数字、下划线）
package.name = schedulemanager

# 域名（反向域名格式）
package.domain = org.myapp

# 源代码目录
source.dir = .

# 包含的文件扩展名
source.include_exts = py,kv,json,png

# 排除的文件/文件夹
source.exclude_dirs = tests, bin, .git, __pycache__, .venv, build, dist, .github, .buildozer

# 应用版本
version = 1.0.0

# Python 依赖
requirements = python3,kivy

# 应用图标
icon.filename = icon.png

# 屏幕方向
orientation = portrait

# 是否全屏
fullscreen = 0

# Android 权限
android.permissions = INTERNET

# Android API 版本
android.api = 31

# 最低支持的 Android API 版本
android.minapi = 21

# Android NDK API 版本
android.ndk_api = 21

# 使用的 Android 架构 (只用一个加快构建速度)
android.archs = arm64-v8a

# 是否接受 SDK 许可证
android.accept_sdk_license = True

# 应用主题颜色
android.presplash_color = #FFFFFF

[buildozer]

# Buildozer 日志级别
log_level = 2

# 构建警告是否视为错误
warn_on_root = 0

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
source.include_exts = py,kv,json

# 包含的文件夹
source.include_patterns = data/*

# 排除的文件/文件夹
source.exclude_dirs = tests, bin, .git, __pycache__, .venv, build, dist
source.exclude_patterns = *.pyc, *.pyo, *.spec

# 应用版本
version = 1.0.0

# Python 依赖
requirements = python3,kivy

# 应用图标（可选，放一个 icon.png 在项目根目录）
#icon.filename = icon.png

# 启动画面（可选）
#presplash.filename = presplash.png

# 屏幕方向：portrait（竖屏）、landscape（横屏）、all（自动）
orientation = portrait

# 是否全屏
fullscreen = 0

# Android 特定配置
[app:android]

# Android 权限
android.permissions = INTERNET,VIBRATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS

# Android API 版本
android.api = 33

# 最低支持的 Android API 版本（Android 5.0+）
android.minapi = 21

# Android NDK API 版本
android.ndk_api = 21

# Android SDK 版本（留空自动下载）
#android.sdk =

# Android NDK 版本（留空自动下载）
#android.ndk = 25b

# 使用的 Android 架构
android.archs = arm64-v8a, armeabi-v7a

# 是否接受 SDK 许可证
android.accept_sdk_license = True

# Gradle 依赖（如需要）
#android.gradle_dependencies =

# 是否启用 AndroidX
android.enable_androidx = True

# 日志级别（调试用）
android.logcat_filters = *:S python:D

# 应用主题颜色
android.presplash_color = #FFFFFF

# iOS 特定配置（如果需要打包 iOS）
[app:ios]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Buildozer 配置
[buildozer]

# Buildozer 日志级别（0=错误，1=信息，2=调试）
log_level = 2

# 构建警告是否视为错误
warn_on_root = 0

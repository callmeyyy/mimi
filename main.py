"""
日程管理助手 - 主入口
使用 Kivy 框架构建跨平台 GUI 应用
"""
import os
import sys

from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import get_color_from_hex

# 导入视图
from views.calendar_view import CalendarView
from views.schedule_view import ScheduleView
from views.plan_view import PlanView
from views.stats_view import StatsView
from views.category_view import CategoryView
from reminder import ReminderService

# 设置窗口大小
Window.size = (400, 700)
Window.minimum_width = 350
Window.minimum_height = 500

# 注册支持 Emoji 的字体
# Segoe UI Emoji 支持 emoji，SDL2 会自动回退到系统字体显示中文
EMOJI_FONT = 'C:/Windows/Fonts/seguiemj.ttf'  # Segoe UI Emoji

if os.path.exists(EMOJI_FONT):
    LabelBase.register(name='Roboto', fn_regular=EMOJI_FONT)

# 加载 KV 文件
Builder.load_file('schedule.kv')


class NavButton(Button):
    """底部导航按钮"""
    screen_name = StringProperty('')
    icon_text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''


class MainLayout(BoxLayout):
    """主布局"""
    screen_manager = ObjectProperty(None)
    current_nav = StringProperty('schedule')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # 创建 ScreenManager
        self.screen_manager = ScreenManager(transition=SlideTransition(duration=0.2))

        # 添加各个视图
        self.screen_manager.add_widget(CalendarView(name='calendar'))
        self.screen_manager.add_widget(ScheduleView(name='schedule'))
        self.screen_manager.add_widget(PlanView(name='plan'))
        self.screen_manager.add_widget(StatsView(name='stats'))
        self.screen_manager.add_widget(CategoryView(name='category'))

        # 默认显示日程视图
        self.screen_manager.current = 'schedule'

        self.add_widget(self.screen_manager)

        # 创建底部导航栏
        self.nav_bar = BoxLayout(
            size_hint_y=None,
            height=60,
            padding=[5, 5],
            spacing=2
        )

        # 导航按钮配置（使用 emoji 图标）
        nav_items = [
            ('calendar', 'Calendar', '📅'),
            ('schedule', 'Schedule', '📋'),
            ('plan', 'Plan', '📊'),
            ('stats', 'Stats', '📈'),
            ('category', 'Category', '🏷'),
        ]

        self.nav_buttons = {}
        for name, label, icon in nav_items:
            btn = NavButton(
                text=f'{icon}\n{label}',
                screen_name=name,
                halign='center',
                valign='middle',
                font_size='12sp',
                color=get_color_from_hex('#666666'),
            )
            btn.bind(on_release=self.on_nav_press)
            self.nav_buttons[name] = btn
            self.nav_bar.add_widget(btn)

        self.add_widget(self.nav_bar)

        # 更新选中状态
        self.update_nav_selection('schedule')

    def on_nav_press(self, button):
        """导航按钮点击"""
        self.screen_manager.current = button.screen_name
        self.update_nav_selection(button.screen_name)

    def update_nav_selection(self, selected):
        """更新导航按钮选中状态"""
        self.current_nav = selected
        for name, btn in self.nav_buttons.items():
            if name == selected:
                btn.color = get_color_from_hex('#4A90D9')
                btn.bold = True
            else:
                btn.color = get_color_from_hex('#666666')
                btn.bold = False


class ScheduleApp(App):
    """日程管理应用"""

    def build(self):
        self.title = '日程管理助手'
        self.main_layout = MainLayout()

        # 启动提醒服务
        self.reminder_service = ReminderService(self.main_layout)
        self.reminder_service.start()

        return self.main_layout

    def on_stop(self):
        """应用退出时停止提醒服务"""
        if hasattr(self, 'reminder_service'):
            self.reminder_service.stop()


if __name__ == '__main__':
    ScheduleApp().run()

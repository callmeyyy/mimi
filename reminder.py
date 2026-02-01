"""
提醒服务 - 使用 Kivy Clock 调度定时检查
每30秒检查到期日程并弹出提醒通知
"""
from kivy.clock import Clock
from views.dialogs import ReminderDialog
from models import data_manager


class ReminderService:
    """提醒服务"""

    def __init__(self, main_layout):
        self.main_layout = main_layout
        self.check_interval = 30  # 检查间隔（秒）
        self.scheduled_event = None
        self.active_dialogs = []

    def start(self):
        """启动提醒服务"""
        # 首次启动时立即检查一次
        Clock.schedule_once(lambda dt: self.check_reminders(), 1)
        # 然后每30秒检查一次
        self.scheduled_event = Clock.schedule_interval(
            lambda dt: self.check_reminders(),
            self.check_interval
        )

    def stop(self):
        """停止提醒服务"""
        if self.scheduled_event:
            self.scheduled_event.cancel()
            self.scheduled_event = None

    def check_reminders(self):
        """检查需要提醒的日程"""
        pending_reminders = data_manager.get_pending_reminders()

        for schedule in pending_reminders:
            # 避免重复弹窗
            schedule_id = schedule['id']
            if any(d.schedule['id'] == schedule_id for d in self.active_dialogs):
                continue

            # 弹出提醒
            self.show_reminder(schedule)

    def show_reminder(self, schedule):
        """显示提醒弹窗"""
        def on_dismiss():
            # 从活跃弹窗列表中移除
            self.active_dialogs = [d for d in self.active_dialogs if d.schedule['id'] != schedule['id']]
            # 刷新视图
            self._refresh_views()

        dialog = ReminderDialog(
            schedule=schedule,
            on_dismiss_callback=on_dismiss
        )
        self.active_dialogs.append(dialog)
        dialog.open()

    def _refresh_views(self):
        """刷新相关视图"""
        if not self.main_layout or not self.main_layout.screen_manager:
            return

        sm = self.main_layout.screen_manager
        current = sm.current

        # 刷新当前视图
        if current == 'calendar':
            screen = sm.get_screen('calendar')
            if hasattr(screen, 'refresh_calendar'):
                screen.refresh_calendar()
            if hasattr(screen, 'refresh_day_schedules'):
                screen.refresh_day_schedules()
        elif current == 'schedule':
            screen = sm.get_screen('schedule')
            if hasattr(screen, 'refresh_list'):
                screen.refresh_list()
        elif current == 'plan':
            screen = sm.get_screen('plan')
            if hasattr(screen, 'refresh_list'):
                screen.refresh_list()
        elif current == 'stats':
            screen = sm.get_screen('stats')
            if hasattr(screen, 'refresh_stats'):
                screen.refresh_stats()

"""
Calendar view - Monthly grid + Daily schedule list
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.clock import Clock
from datetime import datetime, timedelta
import calendar

from models import data_manager
from views.dialogs import ScheduleFormDialog


class DayButton(Button):
    """Day button"""

    def __init__(self, day, is_today=False, is_selected=False, has_events=False,
                 event_colors=None, is_other_month=False, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.is_today = is_today
        self.is_selected = is_selected
        self.has_events = has_events
        self.event_colors = event_colors or []
        self.is_other_month = is_other_month

        self.text = str(day) if day > 0 else ''
        self.font_size = '14sp'
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)

        # Text color
        if is_other_month:
            self.color = get_color_from_hex('#CCCCCC')
        elif is_today:
            self.color = get_color_from_hex('#FFFFFF')
        elif is_selected:
            self.color = get_color_from_hex('#4A90D9')
        else:
            self.color = get_color_from_hex('#333333')

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(lambda dt: self._update_canvas(), 0)

    def _update_canvas(self, *args):
        self.canvas.before.clear()

        with self.canvas.before:
            # Today's background circle
            if self.is_today:
                Color(*get_color_from_hex('#4A90D9'))
                size = min(self.width, self.height) * 0.8
                Ellipse(
                    pos=(self.center_x - size / 2, self.center_y - size / 2),
                    size=(size, size)
                )
            # Selected border
            elif self.is_selected and self.day > 0:
                Color(*get_color_from_hex('#4A90D9'), 0.3)
                size = min(self.width, self.height) * 0.8
                Ellipse(
                    pos=(self.center_x - size / 2, self.center_y - size / 2),
                    size=(size, size)
                )

            # Event indicator dots
            if self.has_events and self.event_colors:
                dot_size = 6
                total_dots = min(len(self.event_colors), 3)
                total_width = total_dots * dot_size + (total_dots - 1) * 3
                start_x = self.center_x - total_width / 2

                for i, color in enumerate(self.event_colors[:3]):
                    Color(*get_color_from_hex(color))
                    Ellipse(
                        pos=(start_x + i * (dot_size + 3), self.y + 5),
                        size=(dot_size, dot_size)
                    )


class CalendarView(Screen):
    """Calendar view"""

    current_month_str = StringProperty('')
    selected_date_str = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today.strftime('%Y-%m-%d')
        self.update_month_str()
        self.update_selected_str()

    def update_month_str(self):
        self.current_month_str = f'{self.current_year}-{self.current_month:02d}'

    def update_selected_str(self):
        try:
            dt = datetime.strptime(self.selected_date, '%Y-%m-%d')
            weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
            self.selected_date_str = f'{dt.month:02d}-{dt.day:02d} {weekday}'
        except ValueError:
            self.selected_date_str = self.selected_date

    def on_enter(self):
        """Refresh on enter"""
        Clock.schedule_once(lambda dt: self.refresh_calendar(), 0.1)
        Clock.schedule_once(lambda dt: self.refresh_day_schedules(), 0.2)

    def refresh_calendar(self):
        """Refresh calendar grid"""
        grid = self.ids.get('calendar_grid')
        if not grid:
            return

        grid.clear_widgets()

        # Get this month's info
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')

        # Get first day of month weekday (0=Monday)
        first_day = datetime(self.current_year, self.current_month, 1)
        first_weekday = first_day.weekday()  # 0-6, Monday to Sunday

        # Convert to Sunday start (0=Sunday)
        first_weekday = (first_weekday + 1) % 7

        # Get days in month
        _, days_in_month = calendar.monthrange(self.current_year, self.current_month)

        # Get this month's schedules
        month_schedules = data_manager.get_schedules_by_month(self.current_year, self.current_month)

        # Previous month days (for displaying last month's dates)
        if self.current_month == 1:
            prev_year, prev_month = self.current_year - 1, 12
        else:
            prev_year, prev_month = self.current_year, self.current_month - 1
        _, prev_days = calendar.monthrange(prev_year, prev_month)

        # Fill previous month dates
        for i in range(first_weekday):
            day = prev_days - first_weekday + i + 1
            btn = DayButton(day, is_other_month=True)
            grid.add_widget(btn)

        # Fill this month dates
        for day in range(1, days_in_month + 1):
            date_str = f'{self.current_year:04d}-{self.current_month:02d}-{day:02d}'

            # Check if has schedules
            day_schedules = month_schedules.get(date_str, [])
            has_events = len(day_schedules) > 0
            event_colors = []
            if has_events:
                # Collect different category colors
                seen_cats = set()
                for s in day_schedules:
                    cat = s.get('category', 'Other')
                    if cat not in seen_cats:
                        seen_cats.add(cat)
                        event_colors.append(data_manager.get_category_color(cat))

            btn = DayButton(
                day,
                is_today=(date_str == today_str),
                is_selected=(date_str == self.selected_date),
                has_events=has_events,
                event_colors=event_colors
            )
            btn.bind(on_release=lambda b, d=date_str: self.on_day_select(d))
            grid.add_widget(btn)

        # Fill next month dates
        total_cells = first_weekday + days_in_month
        remaining = (7 - total_cells % 7) % 7
        for i in range(1, remaining + 1):
            btn = DayButton(i, is_other_month=True)
            grid.add_widget(btn)

    def refresh_day_schedules(self):
        """Refresh daily schedule list"""
        day_list = self.ids.get('day_schedules')
        if not day_list:
            return

        day_list.clear_widgets()

        schedules = data_manager.get_schedules_by_date(self.selected_date)

        if not schedules:
            empty_label = Label(
                text='No schedules today',
                font_size='13sp',
                color=get_color_from_hex('#999999'),
                size_hint_y=None,
                height=50
            )
            day_list.add_widget(empty_label)
            return

        for schedule in schedules:
            card = self._create_schedule_item(schedule)
            day_list.add_widget(card)

    def _create_schedule_item(self, schedule):
        """Create schedule item"""
        item = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            padding=[10, 5],
            spacing=10
        )

        # Background
        with item.canvas.before:
            Color(1, 1, 1, 1)
            item.bg_rect = RoundedRectangle(radius=[8])

        def update_rect(*args):
            item.bg_rect.pos = item.pos
            item.bg_rect.size = item.size

        item.bind(pos=update_rect, size=update_rect)

        # Category color bar
        cat_color = data_manager.get_category_color(schedule.get('category', 'Other'))
        color_bar = Widget(size_hint_x=None, width=4)
        with color_bar.canvas:
            Color(*get_color_from_hex(cat_color))
            color_bar.rect = RoundedRectangle(radius=[2])

        def update_bar(*args):
            color_bar.rect.pos = color_bar.pos
            color_bar.rect.size = color_bar.size

        color_bar.bind(pos=update_bar, size=update_bar)
        item.add_widget(color_bar)

        # Time
        start = schedule.get('start_time', '')
        time_str = start.split(' ')[-1] if ' ' in start else ''
        time_label = Label(
            text=time_str,
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            size_hint_x=None,
            width=50
        )
        item.add_widget(time_label)

        # Title
        status = schedule.get('status', 'pending')
        status_icon = {'pending': '[ ]', 'in_progress': '[~]', 'completed': '[v]', 'cancelled': '[x]'}.get(status, '[ ]')
        title_label = Label(
            text=f"{status_icon} {schedule.get('title', '')}",
            font_size='13sp',
            color=get_color_from_hex('#333333'),
            halign='left',
            text_size=(None, None)
        )
        title_label.bind(size=lambda *x: setattr(title_label, 'text_size', (title_label.width, None)))
        item.add_widget(title_label)

        # Edit button
        edit_btn = Button(
            text='Edit',
            size_hint_x=None,
            width=45,
            font_size='11sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        edit_btn.bind(on_release=lambda b, s=schedule: self.edit_schedule(s))
        item.add_widget(edit_btn)

        return item

    def on_day_select(self, date_str):
        """Select date"""
        self.selected_date = date_str
        self.update_selected_str()
        self.refresh_calendar()
        self.refresh_day_schedules()

    def prev_month(self):
        """Previous month"""
        if self.current_month == 1:
            self.current_year -= 1
            self.current_month = 12
        else:
            self.current_month -= 1
        self.update_month_str()
        self.refresh_calendar()

    def next_month(self):
        """Next month"""
        if self.current_month == 12:
            self.current_year += 1
            self.current_month = 1
        else:
            self.current_month += 1
        self.update_month_str()
        self.refresh_calendar()

    def add_schedule(self):
        """Add schedule"""
        dialog = ScheduleFormDialog(
            default_date=self.selected_date,
            on_save=lambda: (self.refresh_calendar(), self.refresh_day_schedules())
        )
        dialog.open()

    def edit_schedule(self, schedule):
        """Edit schedule"""
        dialog = ScheduleFormDialog(
            schedule=schedule,
            on_save=lambda: (self.refresh_calendar(), self.refresh_day_schedules())
        )
        dialog.open()

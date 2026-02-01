"""
Schedule list view - Search, filter, CRUD operations
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock

from models import data_manager
from views.dialogs import ScheduleFormDialog, ConfirmDialog


class ScheduleCard(BoxLayout):
    """Schedule card"""

    def __init__(self, schedule, on_edit=None, on_delete=None, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.schedule = schedule
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete
        self.on_complete_callback = on_complete

        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 100
        self.padding = [12, 10]
        self.spacing = 5

        # Get category color
        cat_color = data_manager.get_category_color(schedule.get('category', 'Other'))
        self.category_color = get_color_from_hex(cat_color)

        # Background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[10])
            Color(*self.category_color)
            self.color_bar = Rectangle()

        self.bind(pos=self._update_rect, size=self._update_rect)

        # Top: Title + Status
        top_row = BoxLayout(size_hint_y=None, height=25)

        title = schedule.get('title', '')
        status = schedule.get('status', 'pending')
        status_icon = {'pending': '[ ]', 'in_progress': '[~]', 'completed': '[v]', 'cancelled': '[x]'}.get(status, '[ ]')

        title_label = Label(
            text=f"{status_icon} {title}",
            font_size='15sp',
            color=get_color_from_hex('#333333'),
            bold=True,
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        title_label.bind(size=lambda *x: setattr(title_label, 'text_size', (title_label.width, None)))
        top_row.add_widget(title_label)

        self.add_widget(top_row)

        # Middle: Time
        time_row = BoxLayout(size_hint_y=None, height=20)
        start = schedule.get('start_time', '')
        end = schedule.get('end_time', '')
        time_text = start
        if end and end != start:
            time_text = f"{start} ~ {end.split(' ')[-1]}"

        time_label = Label(
            text=f"@ {time_text}",
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            halign='left',
            text_size=(None, None)
        )
        time_label.bind(size=lambda *x: setattr(time_label, 'text_size', (time_label.width, None)))
        time_row.add_widget(time_label)

        self.add_widget(time_row)

        # Bottom: Category + Action buttons
        bottom_row = BoxLayout(size_hint_y=None, height=30, spacing=5)

        cat_label = Label(
            text=schedule.get('category', 'Other'),
            font_size='11sp',
            color=self.category_color,
            size_hint_x=None,
            width=60,
            halign='left'
        )
        bottom_row.add_widget(cat_label)

        # Tag display
        tags = schedule.get('tags', [])
        if tags:
            tags_text = ' '.join([f'#{t}' for t in tags[:2]])
            tags_label = Label(
                text=tags_text,
                font_size='10sp',
                color=get_color_from_hex('#999999'),
                halign='left'
            )
            bottom_row.add_widget(tags_label)
        else:
            bottom_row.add_widget(BoxLayout())

        # Action buttons
        if status != 'completed':
            complete_btn = Button(
                text='Done',
                size_hint_x=None,
                width=45,
                font_size='11sp',
                background_color=get_color_from_hex('#50C878')
            )
            complete_btn.bind(on_release=self.on_complete)
            bottom_row.add_widget(complete_btn)

        edit_btn = Button(
            text='Edit',
            size_hint_x=None,
            width=45,
            font_size='11sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        edit_btn.bind(on_release=self.on_edit)
        bottom_row.add_widget(edit_btn)

        delete_btn = Button(
            text='Delete',
            size_hint_x=None,
            width=45,
            font_size='11sp',
            background_color=get_color_from_hex('#E74C3C')
        )
        delete_btn.bind(on_release=self.on_delete)
        bottom_row.add_widget(delete_btn)

        self.add_widget(bottom_row)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.color_bar.pos = (self.x, self.y)
        self.color_bar.size = (4, self.height)

    def on_edit(self, *args):
        if self.on_edit_callback:
            self.on_edit_callback(self.schedule)

    def on_delete(self, *args):
        if self.on_delete_callback:
            self.on_delete_callback(self.schedule)

    def on_complete(self, *args):
        if self.on_complete_callback:
            self.on_complete_callback(self.schedule)


class ScheduleView(Screen):
    """Schedule list view"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_filter = {
            'category': None,
            'status': None,
            'keyword': ''
        }

    def on_enter(self):
        """Refresh on enter"""
        Clock.schedule_once(lambda dt: self.refresh_categories(), 0.1)
        Clock.schedule_once(lambda dt: self.refresh_list(), 0.2)

    def refresh_categories(self):
        """Refresh category dropdown"""
        spinner = self.ids.get('category_filter')
        if spinner:
            categories = ['All Categories'] + [cat['name'] for cat in data_manager.get_categories()]
            spinner.values = categories

    def refresh_list(self):
        """Refresh schedule list"""
        schedule_list = self.ids.get('schedule_list')
        if not schedule_list:
            return

        schedule_list.clear_widgets()

        # Get filtered schedules
        schedules = self._get_filtered_schedules()

        if not schedules:
            empty_label = Label(
                text='No schedules\nClick button below to add',
                font_size='14sp',
                color=get_color_from_hex('#999999'),
                size_hint_y=None,
                height=100,
                halign='center'
            )
            schedule_list.add_widget(empty_label)
            return

        for schedule in schedules:
            card = ScheduleCard(
                schedule,
                on_edit=self.edit_schedule,
                on_delete=self.delete_schedule,
                on_complete=self.complete_schedule
            )
            schedule_list.add_widget(card)

    def _get_filtered_schedules(self):
        """Get filtered schedules"""
        category = self.current_filter.get('category')
        status = self.current_filter.get('status')
        keyword = self.current_filter.get('keyword', '')

        if keyword:
            schedules = data_manager.search_schedules(keyword)
        else:
            schedules = data_manager.get_schedules()

        # Category filter
        if category:
            schedules = [s for s in schedules if s.get('category') == category]

        # Status filter
        if status:
            schedules = [s for s in schedules if s.get('status') == status]

        # Sort by start time
        schedules.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        return schedules

    def on_search(self, text):
        """Search"""
        self.current_filter['keyword'] = text.strip()
        self.refresh_list()

    def on_filter_change(self):
        """Category filter change"""
        spinner = self.ids.get('category_filter')
        if spinner:
            cat = spinner.text
            self.current_filter['category'] = None if cat == 'All Categories' else cat
            self.refresh_list()

    def on_status_filter(self, status):
        """Status filter"""
        self.current_filter['status'] = None if status == 'all' else status
        self.refresh_list()

    def add_schedule(self):
        """Add schedule"""
        dialog = ScheduleFormDialog(on_save=self.refresh_list)
        dialog.open()

    def edit_schedule(self, schedule):
        """Edit schedule"""
        dialog = ScheduleFormDialog(schedule=schedule, on_save=self.refresh_list)
        dialog.open()

    def delete_schedule(self, schedule):
        """Delete schedule"""
        def on_confirm():
            data_manager.delete_schedule(schedule['id'])
            self.refresh_list()

        dialog = ConfirmDialog(
            message=f"Are you sure to delete schedule\n'{schedule.get('title', '')}'?",
            on_confirm=on_confirm
        )
        dialog.open()

    def complete_schedule(self, schedule):
        """Complete schedule"""
        data_manager.complete_schedule(schedule['id'])
        self.refresh_list()

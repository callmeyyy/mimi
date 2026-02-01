"""
Plan view - Plan management, progress tracking
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock

from models import data_manager
from views.dialogs import PlanFormDialog, ScheduleFormDialog, ConfirmDialog


class PlanCard(BoxLayout):
    """Plan card"""

    def __init__(self, plan, on_edit=None, on_delete=None, on_add_schedule=None, **kwargs):
        super().__init__(**kwargs)
        self.plan = plan
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete
        self.on_add_schedule_callback = on_add_schedule
        self.expanded = False

        self.orientation = 'vertical'
        self.size_hint_y = None
        self.padding = [12, 10]
        self.spacing = 8

        # Background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[10])

        self.bind(pos=self._update_rect, size=self._update_rect)

        # Get progress
        progress = data_manager.get_plan_progress(plan['id'])
        self.progress_value = progress['progress']

        # Calculate base height
        self.base_height = 120
        self.height = self.base_height

        self._build_ui(plan, progress)

    def _build_ui(self, plan, progress):
        # Top: Name + Action buttons
        top_row = BoxLayout(size_hint_y=None, height=30, spacing=5)

        name_label = Label(
            text=plan.get('name', ''),
            font_size='16sp',
            color=get_color_from_hex('#333333'),
            bold=True,
            halign='left',
            text_size=(None, None)
        )
        name_label.bind(size=lambda *x: setattr(name_label, 'text_size', (name_label.width, None)))
        top_row.add_widget(name_label)

        edit_btn = Button(
            text='Edit',
            size_hint_x=None,
            width=40,
            font_size='10sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        edit_btn.bind(on_release=self.on_edit)
        top_row.add_widget(edit_btn)

        delete_btn = Button(
            text='Delete',
            size_hint_x=None,
            width=40,
            font_size='10sp',
            background_color=get_color_from_hex('#E74C3C')
        )
        delete_btn.bind(on_release=self.on_delete)
        top_row.add_widget(delete_btn)

        self.add_widget(top_row)

        # Date range
        date_row = BoxLayout(size_hint_y=None, height=20)
        date_label = Label(
            text=f"{plan.get('start_date', '')} ~ {plan.get('end_date', '')}",
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            halign='left',
            text_size=(None, None)
        )
        date_label.bind(size=lambda *x: setattr(date_label, 'text_size', (date_label.width, None)))
        date_row.add_widget(date_label)
        self.add_widget(date_row)

        # Progress bar
        progress_row = BoxLayout(size_hint_y=None, height=25, spacing=10)

        progress_bar = ProgressBar(
            max=100,
            value=self.progress_value
        )
        progress_row.add_widget(progress_bar)

        progress_label = Label(
            text=f"{progress['completed']}/{progress['total']} ({self.progress_value:.0f}%)",
            font_size='11sp',
            color=get_color_from_hex('#4A90D9'),
            size_hint_x=None,
            width=80
        )
        progress_row.add_widget(progress_label)

        self.add_widget(progress_row)

        # Bottom: Category + Expand/Add buttons
        bottom_row = BoxLayout(size_hint_y=None, height=30, spacing=5)

        cat_color = data_manager.get_category_color(plan.get('category', 'Other'))
        cat_label = Label(
            text=plan.get('category', 'Other'),
            font_size='11sp',
            color=get_color_from_hex(cat_color),
            size_hint_x=None,
            width=60
        )
        bottom_row.add_widget(cat_label)

        bottom_row.add_widget(BoxLayout())

        expand_btn = Button(
            text='Expand' if not self.expanded else 'Collapse',
            size_hint_x=None,
            width=80,
            font_size='11sp',
            background_color=get_color_from_hex('#B0B0B0')
        )
        expand_btn.bind(on_release=self.toggle_expand)
        self.expand_btn = expand_btn
        bottom_row.add_widget(expand_btn)

        add_btn = Button(
            text='+ Schedule',
            size_hint_x=None,
            width=60,
            font_size='11sp',
            background_color=get_color_from_hex('#50C878')
        )
        add_btn.bind(on_release=self.on_add_schedule)
        bottom_row.add_widget(add_btn)

        self.add_widget(bottom_row)

        # Associated schedules container (initially hidden)
        self.schedules_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=0,
            spacing=5
        )
        self.add_widget(self.schedules_container)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def toggle_expand(self, *args):
        self.expanded = not self.expanded
        self.expand_btn.text = 'Collapse' if self.expanded else 'Expand'

        if self.expanded:
            self._show_schedules()
        else:
            self._hide_schedules()

    def _show_schedules(self):
        schedules = data_manager.get_plan_schedules(self.plan['id'])
        self.schedules_container.clear_widgets()

        if not schedules:
            empty_label = Label(
                text='No associated schedules',
                font_size='12sp',
                color=get_color_from_hex('#999999'),
                size_hint_y=None,
                height=30
            )
            self.schedules_container.add_widget(empty_label)
            self.schedules_container.height = 30
        else:
            height = 0
            for schedule in schedules:
                item = self._create_schedule_item(schedule)
                self.schedules_container.add_widget(item)
                height += 40

            self.schedules_container.height = height

        self.height = self.base_height + self.schedules_container.height + 10

    def _hide_schedules(self):
        self.schedules_container.clear_widgets()
        self.schedules_container.height = 0
        self.height = self.base_height

    def _create_schedule_item(self, schedule):
        item = BoxLayout(
            size_hint_y=None,
            height=35,
            padding=[5, 2],
            spacing=5
        )

        # Status icon
        status = schedule.get('status', 'pending')
        status_icon = {'pending': '[ ]', 'in_progress': '[~]', 'completed': '[v]', 'cancelled': '[x]'}.get(status, '[ ]')

        # Color
        cat_color = data_manager.get_category_color(schedule.get('category', 'Other'))

        info_label = Label(
            text=f"{status_icon} {schedule.get('title', '')}",
            font_size='12sp',
            color=get_color_from_hex('#333333'),
            halign='left',
            text_size=(None, None)
        )
        info_label.bind(size=lambda *x: setattr(info_label, 'text_size', (info_label.width, None)))
        item.add_widget(info_label)

        time_label = Label(
            text=schedule.get('start_time', '').split(' ')[-1],
            font_size='10sp',
            color=get_color_from_hex('#666666'),
            size_hint_x=None,
            width=50
        )
        item.add_widget(time_label)

        if status != 'completed':
            complete_btn = Button(
                text='Done',
                size_hint_x=None,
                width=40,
                font_size='10sp',
                background_color=get_color_from_hex('#50C878')
            )
            complete_btn.bind(on_release=lambda b, s=schedule: self.complete_schedule(s))
            item.add_widget(complete_btn)

        return item

    def complete_schedule(self, schedule):
        data_manager.complete_schedule(schedule['id'])
        if self.expanded:
            self._show_schedules()
        # Refresh progress
        progress = data_manager.get_plan_progress(self.plan['id'])
        self.progress_value = progress['progress']

    def on_edit(self, *args):
        if self.on_edit_callback:
            self.on_edit_callback(self.plan)

    def on_delete(self, *args):
        if self.on_delete_callback:
            self.on_delete_callback(self.plan)

    def on_add_schedule(self, *args):
        if self.on_add_schedule_callback:
            self.on_add_schedule_callback(self.plan)


class PlanView(Screen):
    """Plan view"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """Refresh on enter"""
        Clock.schedule_once(lambda dt: self.refresh_list(), 0.1)

    def refresh_list(self):
        """Refresh plan list"""
        plan_list = self.ids.get('plan_list')
        if not plan_list:
            return

        plan_list.clear_widgets()

        plans = data_manager.get_plans()

        if not plans:
            empty_label = Label(
                text='No plans\nClick button below to create',
                font_size='14sp',
                color=get_color_from_hex('#999999'),
                size_hint_y=None,
                height=100,
                halign='center'
            )
            plan_list.add_widget(empty_label)
            return

        for plan in plans:
            card = PlanCard(
                plan,
                on_edit=self.edit_plan,
                on_delete=self.delete_plan,
                on_add_schedule=self.add_schedule_to_plan
            )
            plan_list.add_widget(card)

    def add_plan(self):
        """Add plan"""
        dialog = PlanFormDialog(on_save=self.refresh_list)
        dialog.open()

    def edit_plan(self, plan):
        """Edit plan"""
        dialog = PlanFormDialog(plan=plan, on_save=self.refresh_list)
        dialog.open()

    def delete_plan(self, plan):
        """Delete plan"""
        def on_confirm():
            data_manager.delete_plan(plan['id'])
            self.refresh_list()

        dialog = ConfirmDialog(
            message=f"Are you sure to delete plan\n'{plan.get('name', '')}'?\n(Related schedules won't be deleted)",
            on_confirm=on_confirm
        )
        dialog.open()

    def add_schedule_to_plan(self, plan):
        """Add schedule to plan"""
        dialog = ScheduleFormDialog(
            plan_id=plan['id'],
            default_date=plan.get('start_date'),
            on_save=self.refresh_list
        )
        dialog.open()

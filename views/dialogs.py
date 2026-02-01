"""
Dialog components - Schedule form, confirm dialog, reminder notification, etc.
"""
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from datetime import datetime, timedelta

from models import data_manager


class BaseDialog(ModalView):
    """Base dialog"""

    def __init__(self, title='', **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, None)
        self.height = 400
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.5)

        # Main container
        self.container = BoxLayout(
            orientation='vertical',
            padding=20,
            spacing=15
        )

        with self.container.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[15])

        self.container.bind(pos=self._update_rect, size=self._update_rect)

        # Title
        self.title_label = Label(
            text=title,
            font_size='18sp',
            color=get_color_from_hex('#333333'),
            bold=True,
            size_hint_y=None,
            height=40
        )
        self.container.add_widget(self.title_label)

        # Content area (override in subclass)
        self.content_area = BoxLayout(orientation='vertical', spacing=10)
        self.container.add_widget(self.content_area)

        # Button area
        self.button_area = BoxLayout(
            size_hint_y=None,
            height=45,
            spacing=10
        )
        self.container.add_widget(self.button_area)

        self.add_widget(self.container)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.container.pos
        self.bg_rect.size = self.container.size


class ConfirmDialog(BaseDialog):
    """Confirm dialog"""

    def __init__(self, message='Are you sure to proceed?', on_confirm=None, **kwargs):
        super().__init__(title='Confirm', **kwargs)
        self.height = 200
        self.on_confirm_callback = on_confirm

        # Message
        msg_label = Label(
            text=message,
            font_size='14sp',
            color=get_color_from_hex('#666666'),
            text_size=(None, None),
            halign='center'
        )
        self.content_area.add_widget(msg_label)

        # Buttons
        cancel_btn = Button(
            text='Cancel',
            font_size='14sp',
            background_color=get_color_from_hex('#B0B0B0')
        )
        cancel_btn.bind(on_release=self.dismiss)

        confirm_btn = Button(
            text='Confirm',
            font_size='14sp',
            background_color=get_color_from_hex('#E74C3C')
        )
        confirm_btn.bind(on_release=self.on_confirm)

        self.button_area.add_widget(cancel_btn)
        self.button_area.add_widget(confirm_btn)

    def on_confirm(self, *args):
        if self.on_confirm_callback:
            self.on_confirm_callback()
        self.dismiss()


class ReminderDialog(BaseDialog):
    """Reminder dialog"""

    def __init__(self, schedule, on_dismiss_callback=None, **kwargs):
        super().__init__(title='[!] Schedule Reminder', **kwargs)
        self.height = 280
        self.schedule = schedule
        self.on_dismiss_callback = on_dismiss_callback

        # Schedule title
        title_label = Label(
            text=schedule.get('title', ''),
            font_size='16sp',
            color=get_color_from_hex('#333333'),
            bold=True,
            size_hint_y=None,
            height=30
        )
        self.content_area.add_widget(title_label)

        # Time
        time_label = Label(
            text=f"Start Time: {schedule.get('start_time', '')}",
            font_size='14sp',
            color=get_color_from_hex('#4A90D9'),
            size_hint_y=None,
            height=25
        )
        self.content_area.add_widget(time_label)

        # Description
        desc = schedule.get('description', '')
        if desc:
            desc_label = Label(
                text=desc,
                font_size='12sp',
                color=get_color_from_hex('#666666'),
                text_size=(None, None),
                size_hint_y=None,
                height=40
            )
            self.content_area.add_widget(desc_label)

        # Category
        category = schedule.get('category', 'Other')
        cat_color = data_manager.get_category_color(category)
        cat_label = Label(
            text=f"Category: {category}",
            font_size='12sp',
            color=get_color_from_hex(cat_color),
            size_hint_y=None,
            height=25
        )
        self.content_area.add_widget(cat_label)

        # Buttons
        dismiss_btn = Button(
            text='OK',
            font_size='14sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        dismiss_btn.bind(on_release=self.on_dismiss)

        complete_btn = Button(
            text='Mark Done',
            font_size='14sp',
            background_color=get_color_from_hex('#50C878')
        )
        complete_btn.bind(on_release=self.on_complete)

        self.button_area.add_widget(dismiss_btn)
        self.button_area.add_widget(complete_btn)

    def on_dismiss(self, *args):
        # Mark as reminded
        data_manager.mark_reminded(self.schedule['id'])
        if self.on_dismiss_callback:
            self.on_dismiss_callback()
        self.dismiss()

    def on_complete(self, *args):
        # Mark as completed
        data_manager.complete_schedule(self.schedule['id'])
        data_manager.mark_reminded(self.schedule['id'])
        if self.on_dismiss_callback:
            self.on_dismiss_callback()
        self.dismiss()


class ScheduleFormDialog(BaseDialog):
    """Schedule form dialog"""

    def __init__(self, schedule=None, on_save=None, default_date=None, plan_id=None, **kwargs):
        self.schedule = schedule
        self.on_save_callback = on_save
        self.plan_id = plan_id
        is_edit = schedule is not None

        super().__init__(title='Edit Schedule' if is_edit else 'New Schedule', **kwargs)
        self.height = 520

        # Create scroll view
        scroll = ScrollView(size_hint=(1, 1))
        form_layout = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_y=None,
            padding=[0, 10]
        )
        form_layout.bind(minimum_height=form_layout.setter('height'))

        # Title
        form_layout.add_widget(self._create_label('Title *'))
        self.title_input = TextInput(
            text=schedule.get('title', '') if schedule else '',
            hint_text='Enter schedule title',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.title_input)

        # Description
        form_layout.add_widget(self._create_label('Description'))
        self.desc_input = TextInput(
            text=schedule.get('description', '') if schedule else '',
            hint_text='Enter schedule description',
            multiline=True,
            font_size='14sp',
            size_hint_y=None,
            height=60,
            padding=[10, 10]
        )
        form_layout.add_widget(self.desc_input)

        # Category
        form_layout.add_widget(self._create_label('Category'))
        categories = [cat['name'] for cat in data_manager.get_categories()]
        current_cat = schedule.get('category', 'Other') if schedule else 'Other'
        self.category_spinner = Spinner(
            text=current_cat,
            values=categories,
            font_size='14sp',
            size_hint_y=None,
            height=40
        )
        form_layout.add_widget(self.category_spinner)

        # Start Time
        form_layout.add_widget(self._create_label('Start Time *'))
        if schedule:
            start = schedule.get('start_time', '')
        elif default_date:
            start = f"{default_date} 09:00"
        else:
            start = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.start_input = TextInput(
            text=start,
            hint_text='Format: 2026-02-03 09:00',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.start_input)

        # End Time
        form_layout.add_widget(self._create_label('End Time'))
        end = schedule.get('end_time', '') if schedule else ''
        self.end_input = TextInput(
            text=end,
            hint_text='Format: 2026-02-03 11:00',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.end_input)

        # All Day
        all_day_row = BoxLayout(size_hint_y=None, height=35, spacing=10)
        all_day_row.add_widget(self._create_label('All Day'))
        self.all_day_check = CheckBox(
            active=schedule.get('all_day', False) if schedule else False,
            size_hint_x=None,
            width=40
        )
        all_day_row.add_widget(self.all_day_check)
        all_day_row.add_widget(BoxLayout())  # Placeholder
        form_layout.add_widget(all_day_row)

        # Reminder
        form_layout.add_widget(self._create_label('Reminder'))
        remind = schedule.get('remind_minutes', 0) if schedule else 15
        self.remind_spinner = Spinner(
            text=self._remind_to_text(remind),
            values=['No reminder', '5 min', '10 min', '15 min', '30 min', '1 hour', '2 hours', '1 day'],
            font_size='14sp',
            size_hint_y=None,
            height=40
        )
        form_layout.add_widget(self.remind_spinner)

        # Tags
        form_layout.add_widget(self._create_label('Tags (comma separated)'))
        tags = schedule.get('tags', []) if schedule else []
        self.tags_input = TextInput(
            text=', '.join(tags),
            hint_text='e.g. Important, Urgent',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.tags_input)

        scroll.add_widget(form_layout)
        self.content_area.add_widget(scroll)

        # Buttons
        cancel_btn = Button(
            text='Cancel',
            font_size='14sp',
            background_color=get_color_from_hex('#B0B0B0')
        )
        cancel_btn.bind(on_release=self.dismiss)

        save_btn = Button(
            text='Save',
            font_size='14sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        save_btn.bind(on_release=self.on_save)

        self.button_area.add_widget(cancel_btn)
        self.button_area.add_widget(save_btn)

    def _create_label(self, text):
        label = Label(
            text=text,
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            size_hint_y=None,
            height=22,
            halign='left',
            valign='middle'
        )
        label.bind(size=lambda *x: setattr(label, 'text_size', (label.width, label.height)))
        return label

    def _remind_to_text(self, minutes):
        if minutes <= 0:
            return 'No reminder'
        elif minutes == 5:
            return '5 min'
        elif minutes == 10:
            return '10 min'
        elif minutes == 15:
            return '15 min'
        elif minutes == 30:
            return '30 min'
        elif minutes == 60:
            return '1 hour'
        elif minutes == 120:
            return '2 hours'
        elif minutes == 1440:
            return '1 day'
        return f'{minutes} min'

    def _text_to_remind(self, text):
        mapping = {
            'No reminder': 0,
            '5 min': 5,
            '10 min': 10,
            '15 min': 15,
            '30 min': 30,
            '1 hour': 60,
            '2 hours': 120,
            '1 day': 1440
        }
        return mapping.get(text, 0)

    def on_save(self, *args):
        title = self.title_input.text.strip()
        if not title:
            return  # Title required

        start_time = self.start_input.text.strip()
        if not start_time:
            return  # Start time required

        # Parse tags
        tags_text = self.tags_input.text.strip()
        tags = [t.strip() for t in tags_text.split(',') if t.strip()] if tags_text else []

        data = {
            'title': title,
            'description': self.desc_input.text.strip(),
            'category': self.category_spinner.text,
            'start_time': start_time,
            'end_time': self.end_input.text.strip() or start_time,
            'all_day': self.all_day_check.active,
            'remind_minutes': self._text_to_remind(self.remind_spinner.text),
            'tags': tags
        }

        if self.schedule:
            # Update
            data_manager.update_schedule(self.schedule['id'], **data)
        else:
            # Create new
            if self.plan_id:
                data['plan_id'] = self.plan_id
            data_manager.add_schedule(**data)

        if self.on_save_callback:
            self.on_save_callback()
        self.dismiss()


class PlanFormDialog(BaseDialog):
    """Plan form dialog"""

    def __init__(self, plan=None, on_save=None, **kwargs):
        self.plan = plan
        self.on_save_callback = on_save
        is_edit = plan is not None

        super().__init__(title='Edit Plan' if is_edit else 'New Plan', **kwargs)
        self.height = 380

        # Form
        form_layout = BoxLayout(orientation='vertical', spacing=10)

        # Name
        form_layout.add_widget(self._create_label('Plan Name *'))
        self.name_input = TextInput(
            text=plan.get('name', '') if plan else '',
            hint_text='Enter plan name',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.name_input)

        # Description
        form_layout.add_widget(self._create_label('Description'))
        self.desc_input = TextInput(
            text=plan.get('description', '') if plan else '',
            hint_text='Enter plan description',
            multiline=True,
            font_size='14sp',
            size_hint_y=None,
            height=50,
            padding=[10, 10]
        )
        form_layout.add_widget(self.desc_input)

        # Category
        form_layout.add_widget(self._create_label('Category'))
        categories = [cat['name'] for cat in data_manager.get_categories()]
        current_cat = plan.get('category', 'Other') if plan else 'Other'
        self.category_spinner = Spinner(
            text=current_cat,
            values=categories,
            font_size='14sp',
            size_hint_y=None,
            height=40
        )
        form_layout.add_widget(self.category_spinner)

        # Date range
        date_row = BoxLayout(size_hint_y=None, height=65, spacing=10)

        start_col = BoxLayout(orientation='vertical')
        start_col.add_widget(self._create_label('Start Date'))
        start_date = plan.get('start_date', '') if plan else datetime.now().strftime('%Y-%m-%d')
        self.start_input = TextInput(
            text=start_date,
            hint_text='2026-02-01',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        start_col.add_widget(self.start_input)
        date_row.add_widget(start_col)

        end_col = BoxLayout(orientation='vertical')
        end_col.add_widget(self._create_label('End Date'))
        end_date = plan.get('end_date', '') if plan else (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        self.end_input = TextInput(
            text=end_date,
            hint_text='2026-02-28',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        end_col.add_widget(self.end_input)
        date_row.add_widget(end_col)

        form_layout.add_widget(date_row)
        self.content_area.add_widget(form_layout)

        # Buttons
        cancel_btn = Button(
            text='Cancel',
            font_size='14sp',
            background_color=get_color_from_hex('#B0B0B0')
        )
        cancel_btn.bind(on_release=self.dismiss)

        save_btn = Button(
            text='Save',
            font_size='14sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        save_btn.bind(on_release=self.on_save)

        self.button_area.add_widget(cancel_btn)
        self.button_area.add_widget(save_btn)

    def _create_label(self, text):
        label = Label(
            text=text,
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            size_hint_y=None,
            height=22,
            halign='left',
            valign='middle'
        )
        label.bind(size=lambda *x: setattr(label, 'text_size', (label.width, label.height)))
        return label

    def on_save(self, *args):
        name = self.name_input.text.strip()
        if not name:
            return

        start_date = self.start_input.text.strip()
        end_date = self.end_input.text.strip()
        if not start_date or not end_date:
            return

        data = {
            'name': name,
            'description': self.desc_input.text.strip(),
            'category': self.category_spinner.text,
            'start_date': start_date,
            'end_date': end_date
        }

        if self.plan:
            data_manager.update_plan(self.plan['id'], **data)
        else:
            data_manager.add_plan(**data)

        if self.on_save_callback:
            self.on_save_callback()
        self.dismiss()


class CategoryFormDialog(BaseDialog):
    """Category form dialog"""

    def __init__(self, category=None, on_save=None, **kwargs):
        self.category = category
        self.on_save_callback = on_save
        is_edit = category is not None

        super().__init__(title='Edit Category' if is_edit else 'New Category', **kwargs)
        self.height = 280

        # Form
        form_layout = BoxLayout(orientation='vertical', spacing=10)

        # Name
        form_layout.add_widget(self._create_label('Category Name *'))
        self.name_input = TextInput(
            text=category.get('name', '') if category else '',
            hint_text='Enter category name',
            multiline=False,
            font_size='14sp',
            size_hint_y=None,
            height=40,
            padding=[10, 10]
        )
        form_layout.add_widget(self.name_input)

        # Color
        form_layout.add_widget(self._create_label('Color'))

        # More color options, displayed in two rows
        colors_row1 = ['#4A90D9', '#50C878', '#FFB347', '#E74C3C', '#9B59B6', '#1ABC9C']
        colors_row2 = ['#F39C12', '#3498DB', '#E91E63', '#00BCD4', '#795548', '#607D8B']
        all_colors = colors_row1 + colors_row2

        current_color = category.get('color', '#4A90D9') if category else '#4A90D9'
        self.selected_color = current_color
        self.color_buttons = []

        color_container = BoxLayout(orientation='vertical', size_hint_y=None, height=80, spacing=5)

        for row_colors in [colors_row1, colors_row2]:
            color_row = BoxLayout(size_hint_y=None, height=35, spacing=5)
            for color in row_colors:
                btn = Button(
                    text='',
                    background_color=get_color_from_hex(color),
                    size_hint_x=1
                )
                btn.color_value = color
                btn.bind(on_release=self.on_color_select)
                if color == current_color:
                    btn.text = 'V'
                self.color_buttons.append(btn)
                color_row.add_widget(btn)
            color_container.add_widget(color_row)

        form_layout.add_widget(color_container)
        self.content_area.add_widget(form_layout)

        # Buttons
        cancel_btn = Button(
            text='Cancel',
            font_size='14sp',
            background_color=get_color_from_hex('#B0B0B0')
        )
        cancel_btn.bind(on_release=self.dismiss)

        save_btn = Button(
            text='Save',
            font_size='14sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        save_btn.bind(on_release=self.on_save)

        self.button_area.add_widget(cancel_btn)
        self.button_area.add_widget(save_btn)

    def _create_label(self, text):
        label = Label(
            text=text,
            font_size='12sp',
            color=get_color_from_hex('#666666'),
            size_hint_y=None,
            height=22,
            halign='left',
            valign='middle'
        )
        label.bind(size=lambda *x: setattr(label, 'text_size', (label.width, label.height)))
        return label

    def on_color_select(self, btn):
        self.selected_color = btn.color_value
        for b in self.color_buttons:
            b.text = 'V' if b.color_value == self.selected_color else ''

    def on_save(self, *args):
        name = self.name_input.text.strip()
        if not name:
            return

        if self.category:
            data_manager.update_category(self.category['name'], name, self.selected_color)
        else:
            data_manager.add_category(name, self.selected_color)

        if self.on_save_callback:
            self.on_save_callback()
        self.dismiss()

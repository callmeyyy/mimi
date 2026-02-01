"""
Category management view - Category list, color selection, CRUD
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.clock import Clock

from models import data_manager
from views.dialogs import CategoryFormDialog, ConfirmDialog


class CategoryItem(BoxLayout):
    """Category item"""

    def __init__(self, category, on_edit=None, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self.category = category
        self.on_edit_callback = on_edit
        self.on_delete_callback = on_delete

        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [10, 5]
        self.spacing = 10

        # Background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = RoundedRectangle(radius=[8])

        self.bind(pos=self._update_rect, size=self._update_rect)

        # Color indicator - use AnchorLayout for proper vertical centering
        color_container = AnchorLayout(
            size_hint_x=None,
            width=24,
            anchor_x='center',
            anchor_y='center'
        )
        color_indicator = Widget(size_hint=(None, None), size=(16, 16))
        with color_indicator.canvas:
            Color(*get_color_from_hex(category['color']))
            color_indicator.circle = Ellipse(size=(16, 16))

        def update_circle(*args):
            color_indicator.circle.pos = color_indicator.pos

        color_indicator.bind(pos=update_circle)
        color_container.add_widget(color_indicator)
        self.add_widget(color_container)

        # Category name
        name_label = Label(
            text=category['name'],
            font_size='15sp',
            color=get_color_from_hex('#333333'),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=lambda *x: setattr(name_label, 'text_size', (name_label.width, name_label.height)))
        self.add_widget(name_label)

        # Schedule count
        schedule_count = len(data_manager.get_schedules_by_category(category['name']))
        count_label = Label(
            text=f'{schedule_count} schedules',
            font_size='12sp',
            color=get_color_from_hex('#999999'),
            size_hint_x=None,
            width=70
        )
        self.add_widget(count_label)

        # Edit button
        edit_btn = Button(
            text='Edit',
            size_hint_x=None,
            width=45,
            font_size='11sp',
            background_color=get_color_from_hex('#4A90D9')
        )
        edit_btn.bind(on_release=self.on_edit)
        self.add_widget(edit_btn)

        # Delete button (default categories cannot be deleted)
        if category['name'] not in ['Work', 'Life', 'Study', 'Other']:
            delete_btn = Button(
                text='Delete',
                size_hint_x=None,
                width=45,
                font_size='11sp',
                background_color=get_color_from_hex('#E74C3C')
            )
            delete_btn.bind(on_release=self.on_delete)
            self.add_widget(delete_btn)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_edit(self, *args):
        if self.on_edit_callback:
            self.on_edit_callback(self.category)

    def on_delete(self, *args):
        if self.on_delete_callback:
            self.on_delete_callback(self.category)


class CategoryView(Screen):
    """Category management view"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """Refresh on enter"""
        Clock.schedule_once(lambda dt: self.refresh_list(), 0.1)

    def refresh_list(self):
        """Refresh category list"""
        category_list = self.ids.get('category_list')
        if not category_list:
            return

        category_list.clear_widgets()

        categories = data_manager.get_categories()

        if not categories:
            empty_label = Label(
                text='No categories\nClick button below to add',
                font_size='14sp',
                color=get_color_from_hex('#999999'),
                size_hint_y=None,
                height=100,
                halign='center'
            )
            category_list.add_widget(empty_label)
            return

        for category in categories:
            item = CategoryItem(
                category,
                on_edit=self.edit_category,
                on_delete=self.delete_category
            )
            category_list.add_widget(item)

    def add_category(self):
        """Add category"""
        dialog = CategoryFormDialog(on_save=self.refresh_list)
        dialog.open()

    def edit_category(self, category):
        """Edit category"""
        dialog = CategoryFormDialog(category=category, on_save=self.refresh_list)
        dialog.open()

    def delete_category(self, category):
        """Delete category"""
        def on_confirm():
            data_manager.delete_category(category['name'])
            self.refresh_list()

        dialog = ConfirmDialog(
            message=f"Are you sure to delete category\n'{category['name']}'?\n(Related schedules will be changed to 'Other')",
            on_confirm=on_confirm
        )
        dialog.open()

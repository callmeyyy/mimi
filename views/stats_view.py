"""
统计视图 - 数据统计图表
使用 Canvas 绘制完成率环形图、分类柱状图、趋势折线图
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Line, Ellipse, Rectangle, RoundedRectangle
from kivy.clock import Clock
from math import cos, sin, pi

from models import data_manager


class CompletionChart(Widget):
    """完成率环形图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.completion_rate = 0
        self.bind(pos=self.update_chart, size=self.update_chart)

    def set_data(self, rate):
        self.completion_rate = rate
        self.update_chart()

    def update_chart(self, *args):
        self.canvas.clear()

        with self.canvas:
            # 计算中心和半径
            cx = self.center_x
            cy = self.center_y
            radius = min(self.width, self.height) / 2 - 10
            line_width = 12

            # 背景圆环（灰色）
            Color(*get_color_from_hex('#E0E0E0'))
            Line(circle=(cx, cy, radius), width=line_width)

            # 进度圆环（蓝色）
            if self.completion_rate > 0:
                Color(*get_color_from_hex('#4A90D9'))
                # 从顶部开始（90度），顺时针
                angle_end = 90 - (self.completion_rate / 100) * 360
                Line(
                    circle=(cx, cy, radius, angle_end, 90),
                    width=line_width,
                    cap='round'
                )


class CategoryChart(Widget):
    """分类柱状图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.bind(pos=self.update_chart, size=self.update_chart)

    def set_data(self, data):
        self.data = data
        self.update_chart()

    def update_chart(self, *args):
        self.canvas.clear()

        if not self.data:
            return

        with self.canvas:
            # 过滤有数据的分类
            valid_data = [d for d in self.data if d['count'] > 0]
            if not valid_data:
                Color(*get_color_from_hex('#999999'))
                # 显示无数据提示
                return

            # 计算最大值
            max_count = max(d['count'] for d in valid_data)
            if max_count == 0:
                max_count = 1

            # 计算柱状图参数
            padding = 20
            bar_area_width = self.width - padding * 2
            bar_area_height = self.height - 40

            bar_count = len(valid_data)
            if bar_count == 0:
                return

            bar_width = min(40, (bar_area_width - (bar_count - 1) * 10) / bar_count)
            total_width = bar_count * bar_width + (bar_count - 1) * 10
            start_x = self.x + (self.width - total_width) / 2

            for i, item in enumerate(valid_data):
                x = start_x + i * (bar_width + 10)
                height = (item['count'] / max_count) * bar_area_height

                # 柱状条
                Color(*get_color_from_hex(item['color']))
                RoundedRectangle(
                    pos=(x, self.y + 25),
                    size=(bar_width, max(height, 5)),
                    radius=[5, 5, 0, 0]
                )

                # 数量标签（在柱顶）
                # 使用小矩形表示数字位置
                Color(*get_color_from_hex('#333333'))


class TrendChart(Widget):
    """趋势折线图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.bind(pos=self.update_chart, size=self.update_chart)

    def set_data(self, data):
        self.data = data
        self.update_chart()

    def update_chart(self, *args):
        self.canvas.clear()

        if not self.data or len(self.data) < 2:
            return

        with self.canvas:
            padding = 30
            chart_width = self.width - padding * 2
            chart_height = self.height - padding * 2

            # 计算最大值
            max_total = max(d['total'] for d in self.data) or 1
            max_completed = max(d['completed'] for d in self.data) or 1
            max_val = max(max_total, max_completed, 1)

            # 计算点的位置
            step_x = chart_width / (len(self.data) - 1) if len(self.data) > 1 else chart_width

            # 绘制网格线
            Color(*get_color_from_hex('#E0E0E0'))
            for i in range(5):
                y = self.y + padding + i * (chart_height / 4)
                Line(points=[self.x + padding, y, self.x + self.width - padding, y], width=1)

            # 总数折线（灰色）
            total_points = []
            for i, item in enumerate(self.data):
                x = self.x + padding + i * step_x
                y = self.y + padding + (item['total'] / max_val) * chart_height
                total_points.extend([x, y])

            if len(total_points) >= 4:
                Color(*get_color_from_hex('#B0B0B0'))
                Line(points=total_points, width=2)

            # 完成数折线（蓝色）
            completed_points = []
            for i, item in enumerate(self.data):
                x = self.x + padding + i * step_x
                y = self.y + padding + (item['completed'] / max_val) * chart_height
                completed_points.extend([x, y])

            if len(completed_points) >= 4:
                Color(*get_color_from_hex('#4A90D9'))
                Line(points=completed_points, width=2)

                # 绘制数据点
                for i in range(0, len(completed_points), 2):
                    Ellipse(
                        pos=(completed_points[i] - 4, completed_points[i + 1] - 4),
                        size=(8, 8)
                    )


class StatsView(Screen):
    """统计视图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """进入视图时刷新"""
        Clock.schedule_once(lambda dt: self.refresh_stats(), 0.1)

    def refresh_stats(self):
        """刷新统计数据"""
        # 完成率
        completion_stats = data_manager.get_completion_stats()
        completion_label = self.ids.get('completion_label')
        if completion_label:
            rate = completion_stats['completion_rate']
            completion_label.text = f"{rate:.0f}%"

        # 完成率图表
        completion_chart = self.ids.get('completion_chart')
        if completion_chart:
            # 创建环形图
            self._draw_completion_chart(completion_chart, completion_stats['completion_rate'])

        # 分类分布
        category_stats = data_manager.get_category_stats()
        category_chart = self.ids.get('category_chart')
        if category_chart:
            self._draw_category_chart(category_chart, category_stats)

        # 每日趋势
        daily_stats = data_manager.get_daily_stats(7)
        trend_chart = self.ids.get('trend_chart')
        if trend_chart:
            self._draw_trend_chart(trend_chart, daily_stats)

    def _draw_completion_chart(self, widget, rate):
        """绘制完成率环形图"""
        widget.canvas.clear()

        with widget.canvas:
            cx = widget.center_x
            cy = widget.center_y
            radius = min(widget.width, widget.height) / 2 - 5
            line_width = 10

            # 背景圆环
            Color(*get_color_from_hex('#E0E0E0'))
            Line(circle=(cx, cy, radius), width=line_width)

            # 进度圆环
            if rate > 0:
                Color(*get_color_from_hex('#4A90D9'))
                angle_end = 90 - (rate / 100) * 360
                Line(
                    circle=(cx, cy, radius, angle_end, 90),
                    width=line_width,
                    cap='round'
                )

    def _draw_category_chart(self, widget, data):
        """绘制分类柱状图"""
        widget.canvas.clear()

        # 过滤有数据的分类
        valid_data = [d for d in data if d['count'] > 0]
        if not valid_data:
            with widget.canvas:
                Color(*get_color_from_hex('#999999'))
            return

        max_count = max(d['count'] for d in valid_data) or 1

        with widget.canvas:
            padding = 15
            bar_area_height = widget.height - 30

            bar_count = len(valid_data)
            bar_width = min(35, (widget.width - padding * 2 - (bar_count - 1) * 8) / bar_count)
            total_width = bar_count * bar_width + (bar_count - 1) * 8
            start_x = widget.x + (widget.width - total_width) / 2

            for i, item in enumerate(valid_data):
                x = start_x + i * (bar_width + 8)
                height = (item['count'] / max_count) * bar_area_height

                Color(*get_color_from_hex(item['color']))
                RoundedRectangle(
                    pos=(x, widget.y + 20),
                    size=(bar_width, max(height, 5)),
                    radius=[4, 4, 0, 0]
                )

    def _draw_trend_chart(self, widget, data):
        """绘制趋势折线图"""
        widget.canvas.clear()

        if not data or len(data) < 2:
            return

        with widget.canvas:
            padding_x = 25
            padding_y = 20
            chart_width = widget.width - padding_x * 2
            chart_height = widget.height - padding_y * 2

            max_val = max(max(d['total'] for d in data), max(d['completed'] for d in data), 1)
            step_x = chart_width / (len(data) - 1) if len(data) > 1 else chart_width

            # 网格线
            Color(*get_color_from_hex('#E8E8E8'))
            for i in range(4):
                y = widget.y + padding_y + i * (chart_height / 3)
                Line(points=[widget.x + padding_x, y, widget.x + widget.width - padding_x, y], width=1)

            # 总数折线
            total_points = []
            for i, item in enumerate(data):
                x = widget.x + padding_x + i * step_x
                y = widget.y + padding_y + (item['total'] / max_val) * chart_height
                total_points.extend([x, y])

            if len(total_points) >= 4:
                Color(*get_color_from_hex('#B0B0B0'))
                Line(points=total_points, width=1.5)

            # 完成数折线
            completed_points = []
            for i, item in enumerate(data):
                x = widget.x + padding_x + i * step_x
                y = widget.y + padding_y + (item['completed'] / max_val) * chart_height
                completed_points.extend([x, y])

            if len(completed_points) >= 4:
                Color(*get_color_from_hex('#4A90D9'))
                Line(points=completed_points, width=2)

                for i in range(0, len(completed_points), 2):
                    Ellipse(
                        pos=(completed_points[i] - 3, completed_points[i + 1] - 3),
                        size=(6, 6)
                    )

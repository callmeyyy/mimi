"""
数据模型层 - DataManager 类
负责 JSON 文件读写、日程/计划/分类的 CRUD 操作、统计数据聚合和提醒查询
"""
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path


class DataManager:
    """数据管理器 - 单例模式"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 数据文件路径
        self.data_dir = Path(__file__).parent / "data"
        self.data_file = self.data_dir / "schedules.json"

        # 默认分类
        self.default_categories = [
            {"name": "Work", "color": "#4A90D9"},
            {"name": "Life", "color": "#50C878"},
            {"name": "Study", "color": "#FFB347"},
            {"name": "Other", "color": "#B0B0B0"}
        ]

        # 加载数据
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """加载 JSON 数据文件"""
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)

        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # 返回默认数据结构
        return {
            "categories": self.default_categories.copy(),
            "schedules": [],
            "plans": []
        }

    def _save_data(self):
        """原子写入保存数据"""
        temp_file = self.data_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            # 原子替换
            if os.name == 'nt':  # Windows
                if self.data_file.exists():
                    self.data_file.unlink()
            temp_file.replace(self.data_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e

    # ========== 分类 CRUD ==========

    def get_categories(self) -> List[Dict]:
        """获取所有分类"""
        return self.data.get("categories", [])

    def get_category_color(self, name: str) -> str:
        """根据分类名获取颜色"""
        for cat in self.data.get("categories", []):
            if cat["name"] == name:
                return cat["color"]
        return "#B0B0B0"  # 默认灰色

    def add_category(self, name: str, color: str) -> bool:
        """添加分类"""
        # 检查是否已存在
        for cat in self.data["categories"]:
            if cat["name"] == name:
                return False
        self.data["categories"].append({"name": name, "color": color})
        self._save_data()
        return True

    def update_category(self, old_name: str, new_name: str, color: str) -> bool:
        """更新分类"""
        for cat in self.data["categories"]:
            if cat["name"] == old_name:
                # 更新日程和计划中的分类引用
                if old_name != new_name:
                    for schedule in self.data["schedules"]:
                        if schedule.get("category") == old_name:
                            schedule["category"] = new_name
                    for plan in self.data["plans"]:
                        if plan.get("category") == old_name:
                            plan["category"] = new_name
                cat["name"] = new_name
                cat["color"] = color
                self._save_data()
                return True
        return False

    def delete_category(self, name: str) -> bool:
        """删除分类（将相关日程/计划设为'Other'）"""
        for i, cat in enumerate(self.data["categories"]):
            if cat["name"] == name:
                # 将相关日程和计划改为"Other"
                for schedule in self.data["schedules"]:
                    if schedule.get("category") == name:
                        schedule["category"] = "Other"
                for plan in self.data["plans"]:
                    if plan.get("category") == name:
                        plan["category"] = "Other"
                self.data["categories"].pop(i)
                self._save_data()
                return True
        return False

    # ========== 日程 CRUD ==========

    def get_schedules(self) -> List[Dict]:
        """获取所有日程"""
        return self.data.get("schedules", [])

    def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict]:
        """根据 ID 获取日程"""
        for schedule in self.data["schedules"]:
            if schedule["id"] == schedule_id:
                return schedule
        return None

    def get_schedules_by_date(self, date: str) -> List[Dict]:
        """获取指定日期的日程 (date 格式: 2026-02-03)"""
        result = []
        for schedule in self.data["schedules"]:
            start = schedule.get("start_time", "")
            if start.startswith(date):
                result.append(schedule)
        # 按开始时间排序
        result.sort(key=lambda x: x.get("start_time", ""))
        return result

    def get_schedules_by_month(self, year: int, month: int) -> Dict[str, List[Dict]]:
        """获取指定月份的日程，返回 {日期: [日程列表]}"""
        prefix = f"{year:04d}-{month:02d}"
        result = {}
        for schedule in self.data["schedules"]:
            start = schedule.get("start_time", "")
            if start.startswith(prefix):
                date = start[:10]
                if date not in result:
                    result[date] = []
                result[date].append(schedule)
        return result

    def get_schedules_by_category(self, category: str) -> List[Dict]:
        """获取指定分类的日程"""
        return [s for s in self.data["schedules"] if s.get("category") == category]

    def search_schedules(self, keyword: str) -> List[Dict]:
        """搜索日程（标题、描述、标签）"""
        keyword = keyword.lower()
        result = []
        for schedule in self.data["schedules"]:
            if keyword in schedule.get("title", "").lower():
                result.append(schedule)
            elif keyword in schedule.get("description", "").lower():
                result.append(schedule)
            elif any(keyword in tag.lower() for tag in schedule.get("tags", [])):
                result.append(schedule)
        return result

    def filter_schedules(self, category: str = None, status: str = None,
                        start_date: str = None, end_date: str = None) -> List[Dict]:
        """筛选日程"""
        result = self.data["schedules"].copy()

        if category:
            result = [s for s in result if s.get("category") == category]

        if status:
            result = [s for s in result if s.get("status") == status]

        if start_date:
            result = [s for s in result if s.get("start_time", "") >= start_date]

        if end_date:
            result = [s for s in result if s.get("start_time", "")[:10] <= end_date]

        # 按开始时间排序
        result.sort(key=lambda x: x.get("start_time", ""))
        return result

    def add_schedule(self, title: str, start_time: str, end_time: str = None,
                     description: str = "", category: str = "Other", tags: List[str] = None,
                     all_day: bool = False, remind_minutes: int = 0,
                     plan_id: str = None) -> Dict:
        """添加日程"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        schedule = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "category": category,
            "tags": tags or [],
            "start_time": start_time,
            "end_time": end_time or start_time,
            "all_day": all_day,
            "remind_minutes": remind_minutes,
            "reminded": False,
            "status": "pending",
            "plan_id": plan_id,
            "created_at": now,
            "updated_at": now
        }
        self.data["schedules"].append(schedule)
        self._save_data()
        return schedule

    def update_schedule(self, schedule_id: str, **kwargs) -> bool:
        """更新日程"""
        for schedule in self.data["schedules"]:
            if schedule["id"] == schedule_id:
                for key, value in kwargs.items():
                    if key in schedule:
                        schedule[key] = value
                schedule["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_data()
                return True
        return False

    def delete_schedule(self, schedule_id: str) -> bool:
        """删除日程"""
        for i, schedule in enumerate(self.data["schedules"]):
            if schedule["id"] == schedule_id:
                self.data["schedules"].pop(i)
                self._save_data()
                return True
        return False

    def complete_schedule(self, schedule_id: str) -> bool:
        """标记日程为已完成"""
        return self.update_schedule(schedule_id, status="completed")

    # ========== 计划 CRUD ==========

    def get_plans(self) -> List[Dict]:
        """获取所有计划"""
        return self.data.get("plans", [])

    def get_plan_by_id(self, plan_id: str) -> Optional[Dict]:
        """根据 ID 获取计划"""
        for plan in self.data["plans"]:
            if plan["id"] == plan_id:
                return plan
        return None

    def add_plan(self, name: str, start_date: str, end_date: str,
                 description: str = "", category: str = "Other") -> Dict:
        """添加计划"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plan = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "category": category,
            "start_date": start_date,
            "end_date": end_date,
            "created_at": now
        }
        self.data["plans"].append(plan)
        self._save_data()
        return plan

    def update_plan(self, plan_id: str, **kwargs) -> bool:
        """更新计划"""
        for plan in self.data["plans"]:
            if plan["id"] == plan_id:
                for key, value in kwargs.items():
                    if key in plan:
                        plan[key] = value
                self._save_data()
                return True
        return False

    def delete_plan(self, plan_id: str) -> bool:
        """删除计划（同时解除关联日程）"""
        for i, plan in enumerate(self.data["plans"]):
            if plan["id"] == plan_id:
                # 解除关联日程
                for schedule in self.data["schedules"]:
                    if schedule.get("plan_id") == plan_id:
                        schedule["plan_id"] = None
                self.data["plans"].pop(i)
                self._save_data()
                return True
        return False

    def get_plan_schedules(self, plan_id: str) -> List[Dict]:
        """获取计划关联的日程"""
        return [s for s in self.data["schedules"] if s.get("plan_id") == plan_id]

    def get_plan_progress(self, plan_id: str) -> Dict:
        """计算计划进度"""
        schedules = self.get_plan_schedules(plan_id)
        total = len(schedules)
        if total == 0:
            return {"total": 0, "completed": 0, "progress": 0}

        completed = sum(1 for s in schedules if s.get("status") == "completed")
        return {
            "total": total,
            "completed": completed,
            "progress": round(completed / total * 100, 1)
        }

    # ========== 提醒查询 ==========

    def get_pending_reminders(self) -> List[Dict]:
        """获取需要提醒的日程（到期未提醒）"""
        now = datetime.now()
        result = []

        for schedule in self.data["schedules"]:
            # 跳过已提醒、已完成或已取消的
            if schedule.get("reminded", False):
                continue
            if schedule.get("status") in ("completed", "cancelled"):
                continue

            remind_minutes = schedule.get("remind_minutes", 0)
            if remind_minutes <= 0:
                continue

            try:
                start_time = datetime.strptime(schedule["start_time"], "%Y-%m-%d %H:%M")
                remind_time = start_time - timedelta(minutes=remind_minutes)

                if now >= remind_time and now < start_time:
                    result.append(schedule)
            except (ValueError, KeyError):
                continue

        return result

    def mark_reminded(self, schedule_id: str) -> bool:
        """标记日程已提醒"""
        return self.update_schedule(schedule_id, reminded=True)

    # ========== 统计数据 ==========

    def get_completion_stats(self) -> Dict:
        """获取完成率统计"""
        schedules = self.data["schedules"]
        total = len(schedules)
        if total == 0:
            return {"total": 0, "completed": 0, "pending": 0,
                    "in_progress": 0, "cancelled": 0, "completion_rate": 0}

        completed = sum(1 for s in schedules if s.get("status") == "completed")
        pending = sum(1 for s in schedules if s.get("status") == "pending")
        in_progress = sum(1 for s in schedules if s.get("status") == "in_progress")
        cancelled = sum(1 for s in schedules if s.get("status") == "cancelled")

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "completion_rate": round(completed / total * 100, 1)
        }

    def get_category_stats(self) -> List[Dict]:
        """获取分类分布统计"""
        category_counts = {}
        for schedule in self.data["schedules"]:
            cat = schedule.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        result = []
        for cat in self.data["categories"]:
            name = cat["name"]
            result.append({
                "name": name,
                "color": cat["color"],
                "count": category_counts.get(name, 0)
            })
        return result

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """获取每日趋势统计（最近N天）"""
        result = []
        today = datetime.now().date()

        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            schedules = self.get_schedules_by_date(date_str)

            total = len(schedules)
            completed = sum(1 for s in schedules if s.get("status") == "completed")

            result.append({
                "date": date_str,
                "day": date.strftime("%m-%d"),
                "total": total,
                "completed": completed
            })

        return result


# 全局单例
data_manager = DataManager()

# -*- coding: utf-8 -*-
"""
Генератор всех UML-диаграмм для ИС «Мониторинг KPI Торгового Центра».
Запуск: python -m app.diagrams.generate_all
"""
import math
import html
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Ellipse, Polygon, FancyBboxPatch
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ============================================================================
# ЦВЕТОВАЯ СХЕМА
# ============================================================================
BG = "#F7FBFF"
ENT_FILL = "#DCEBFB"
REL_FILL = "#FCE4D6"
ATT_FILL = "#FFFFFF"
CLS_FILL = "#E8F4FC"
EXT_FILL = "#EFEFEF"
COMP_FILL = "#FFE4E1"
DEPLOY_FILL = "#E0FFE0"
INK = "#1A1A1A"
LINE_CLR = "#444444"

DPI_WIN = 85
TOP_FRAC = 0.07
FS_NAME, FS_STEREO, FS_MEM, FS_CARD, FS_TITLE = 11, 8.5, 8.5, 9, 14
PAD_X, LINE_H, HEAD_H, SEP = 0.5, 0.22, 0.30, 0.04

# ============================================================================
# ДИАГРАММА 1: КЛАССОВ (UML)
# ============================================================================
CLASS_DIAGRAM = {
    "classes": {
        "DockerManager": (2, 14, "", 
            ["+ client: DockerClient", "+ containers: dict"],
            ["+ start_stack()", "+ stop_stack()", "+ wait_for_healthy()"]),
        "StreamProcessor": (6, 14, "",
            ["+ kafka_broker: str", "+ window_size: int", "+ running: bool"],
            ["+ process(callback)", "+ aggregate_metrics()", "+ stop()"]),
        "AlertManager": (10, 14, "",
            ["+ thresholds: dict", "+ telegram_token: str"],
            ["+ check_and_alert(metrics)", "+ send_telegram(msg)", "+ update_thresholds()"]),
        "DataGenerator": (14, 14, "",
            ["+ kafka_broker: str", "+ topic: str", "+ running: bool"],
            ["+ start()", "+ generate_metrics()", "+ stop()"]),
        "ConfigManager": (2, 9, "",
            ["+ config: dict", "+ file_path: str"],
            ["+ get(key, default)", "+ load()"]),
        "KPIMonitorGUI": (6, 9, "",
            ["+ root: CTk", "+ docker_manager: DockerManager", "+ user_info: dict"],
            ["+ _build_header()", "+ _build_tabs()", "+ _toggle_theme()"]),
        "ClickHouseClient": (10, 9, "",
            ["+ host: str", "+ database: str", "+ client: Client"],
            ["+ query(sql)", "+ insert(data)", "+ ensure_tables()"]),
        "LoginFrame": (14, 9, "",
            ["+ entry_login: CTkEntry", "+ entry_pass: CTkEntry"],
            ["+ _build_ui()", "+ _login()"]),
    },
    "edges": [
        ("DockerManager", "StreamProcessor", "assoc", "1", "1"),
        ("DockerManager", "ClickHouseClient", "assoc", "1", "1"),
        ("ConfigManager", "DockerManager", "assoc", "1", "*"),
        ("ConfigManager", "AlertManager", "assoc", "1", "1"),
        ("AlertManager", "StreamProcessor", "assoc", "1", "1"),
        ("DataGenerator", "StreamProcessor", "assoc", "1", "1"),
        ("KPIMonitorGUI", "DockerManager", "comp", "1", "1"),
        ("KPIMonitorGUI", "AlertManager", "assoc", "1", "1"),
        ("LoginFrame", "KPIMonitorGUI", "assoc", "1", "1"),
    ]
}

# ============================================================================
# ДИАГРАММА 2: КОНЦЕПТУАЛЬНАЯ (ЧЕН) - СУЩНОСТИ И СВЯЗИ
# ============================================================================
CHEN_DIAGRAM = {
    "entities": {
        "Пользователь": (2, 12, ["id", "login", "password", "role", "name"], 0, 135),
        "Сессия": (2, 8, ["id", "token", "user_id", "created_at"], 0, 180),
        "Метрика": (7, 12, ["id", "timestamp", "source", "cpu", "errors"], 0, 90),
        "Алерт": (12, 12, ["id", "timestamp", "type", "value", "threshold"], 0, 45),
        "ЗонаТЦ": (7, 7, ["id", "name", "location", "capacity"], 0, 270),
        "Событие": (12, 7, ["id", "timestamp", "zone_id", "type", "description"], 0, 315),
    },
    "relations": [
        ("Пользователь", "1", "Имеет", "N", "Сессия", 2, 10),
        ("Пользователь", "1", "Получает", "N", "Алерт", 7, 10),
        ("ЗонаТЦ", "1", "Генерирует", "N", "Метрика", 5, 9.5),
        ("Метрика", "1", "Вызывает", "N", "Алерт", 10, 10),
        ("ЗонаТЦ", "1", "Содержит", "N", "Событие", 9.5, 7),
        ("Событие", "1", "Влияет", "N", "Метрика", 9.5, 9.5),
    ]
}

# ============================================================================
# ДИАГРАММА 3: КОМПОНЕНТОВ
# ============================================================================
COMPONENT_DIAGRAM = {
    "components": {
        "DataGenerator": (2, 12, "producer", ["Kafka Producer"]),
        "Redpanda/Kafka": (6, 12, "message_broker", ["Topic: tc_metrics"]),
        "StreamProcessor": (10, 12, "processor", ["Windowing", "Aggregation"]),
        "ClickHouse": (14, 12, "database", ["Table: metrics_aggregated"]),
        "AlertManager": (10, 7, "service", ["Telegram Bot API"]),
        "DockerManager": (2, 7, "orchestrator", ["Docker SDK"]),
        "KPIMonitorGUI": (6, 7, "ui", ["CustomTkinter", "Matplotlib"]),
        "ConfigManager": (14, 7, "config", ["settings.json"]),
    },
    "edges": [
        ("DataGenerator", "Redpanda/Kafka", "solid"),
        ("Redpanda/Kafka", "StreamProcessor", "solid"),
        ("StreamProcessor", "ClickHouse", "solid"),
        ("StreamProcessor", "AlertManager", "dashed"),
        ("AlertManager", "Redpanda/Kafka", "dashed"),
        ("DockerManager", "Redpanda/Kafka", "dotted"),
        ("DockerManager", "ClickHouse", "dotted"),
        ("KPIMonitorGUI", "DockerManager", "solid"),
        ("KPIMonitorGUI", "ClickHouse", "solid"),
        ("ConfigManager", "KPIMonitorGUI", "dashed"),
        ("ConfigManager", "StreamProcessor", "dashed"),
    ]
}

# ============================================================================
# ДИАГРАММА 4: РАЗВЕРТЫВАНИЯ
# ============================================================================
DEPLOYMENT_DIAGRAM = {
    "nodes": {
        "Workstation\n(Рабочая станция)": (2, 12, "desktop", 
            ["Python 3.11", "CustomTkinter GUI", "Docker Desktop"]),
        "Docker Container\nRedpanda": (7, 14, "server", 
            ["Port 9092", "Kafka API", "Topic: tc_metrics"]),
        "Docker Container\nClickHouse": (12, 14, "database", 
            ["Port 8123", "DB: kpi_db", "Table: metrics_aggregated"]),
        "Docker Container\nGrafana": (17, 14, "monitoring", 
            ["Port 3000", "Dashboards"]),
        "External\nTelegram API": (17, 7, "cloud", 
            ["Bot API", "HTTPS"]),
        "External\nData Sources": (2, 7, "cloud", 
            ["Sensors", "Logs", "APIs"]),
    },
    "connections": [
        ("Workstation\n(Рабочая станция)", "Docker Container\nRedpanda", "Docker Network"),
        ("Workstation\n(Рабочая станция)", "Docker Container\nClickHouse", "Docker Network"),
        ("Workstation\n(Рабочая станция)", "Docker Container\nGrafana", "Docker Network"),
        ("Docker Container\nRedpanda", "Docker Container\nClickHouse", "Internal"),
        ("Docker Container\nRedpanda", "External\nTelegram API", "HTTPS"),
        ("External\nData Sources", "Docker Container\nRedpanda", "Kafka Protocol"),
    ]
}

# ============================================================================
# ДИАГРАММА 5: ПОСЛЕДОВАТЕЛЬНОСТИ (Упрощенная - запуск системы)
# ============================================================================
SEQUENCE_DIAGRAM = {
    "lifelines": ["User", "KPIMonitorGUI", "DockerManager", "Redpanda", "ClickHouse", "StreamProcessor"],
    "messages": [
        (0, 1, "1. Ввести логин/пароль", "solid"),
        (1, 1, "2. Проверить credentials", "self"),
        (1, 2, "3. start_stack()", "solid"),
        (2, 3, "4. docker run redpanda", "solid"),
        (2, 4, "5. docker run clickhouse", "solid"),
        (3, 3, "6. Initialize broker", "self"),
        (4, 4, "7. Create database", "self"),
        (2, 5, "8. ensure_database_and_tables()", "solid"),
        (1, 5, "9. process(callback)", "solid"),
        (5, 3, "10. Consume messages", "solid"),
        (5, 4, "11. INSERT metrics", "solid"),
        (5, 5, "12. check_and_alert()", "self"),
    ]
}

# ============================================================================
# ДИАГРАММА 6: ВАРИАНТОВ ИСПОЛЬЗОВАНИЯ (АДМИНИСТРАТОР)
# ============================================================================
USECASE_ADMIN = {
    "actors": {
        "Администратор": (1, 10),
    },
    "usecases": {
        "Авторизоваться": (5, 13),
        "Просматривать Dashboard": (9, 13),
        "Управлять пользователями": (13, 13),
        "Настраивать алерты": (17, 13),
        "Просматривать аналитику": (9, 9),
        "Мониторить зоны ТЦ": (13, 9),
        "Управлять инфраструктурой": (17, 9),
        "Экспортировать отчеты": (13, 5),
    },
    "connections": [
        ("Администратор", "Авторизоваться", "assoc"),
        ("Администратор", "Просматривать Dashboard", "assoc"),
        ("Администратор", "Управлять пользователями", "assoc"),
        ("Администратор", "Настраивать алерты", "assoc"),
        ("Администратор", "Просматривать аналитику", "assoc"),
        ("Администратор", "Мониторить зоны ТЦ", "assoc"),
        ("Администратор", "Управлять инфраструктурой", "assoc"),
        ("Администратор", "Экспортировать отчеты", "assoc"),
        ("Авторизоваться", "Просматривать Dashboard", "include"),
    ]
}

# ============================================================================
# ДИАГРАММА 7: ВАРИАНТОВ ИСПОЛЬЗОВАНИЯ (ПОЛЬЗОВАТЕЛЬ/ОПЕРАТОР)
# ============================================================================
USECASE_USER = {
    "actors": {
        "Оператор": (1, 10),
    },
    "usecases": {
        "Авторизоваться": (5, 13),
        "Просматривать Dashboard": (9, 13),
        "Просматривать аналитику": (13, 13),
        "Мониторить зоны ТЦ": (17, 13),
        "Получать алерты": (9, 9),
        "Просматривать детали зон": (13, 9),
        "Переключать тему": (17, 9),
    },
    "connections": [
        ("Оператор", "Авторизоваться", "assoc"),
        ("Оператор", "Просматривать Dashboard", "assoc"),
        ("Оператор", "Просматривать аналитику", "assoc"),
        ("Оператор", "Мониторить зоны ТЦ", "assoc"),
        ("Оператор", "Получать алерты", "assoc"),
        ("Оператор", "Просматривать детали зон", "assoc"),
        ("Оператор", "Переключать тему", "assoc"),
        ("Авторизоваться", "Просматривать Dashboard", "include"),
    ]
}

# ============================================================================
# УТИЛИТЫ
# ============================================================================
def measure(ax, fig, label, fs):
    t = ax.text(0, 0, label, fontsize=fs, ha="center", va="center")
    try:
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
        w, h = bb.width / fig.dpi, bb.height / fig.dpi
    except Exception:
        w = len(label) * 0.62 * fs / 72.0
        h = 1.25 * fs / 72.0
    t.remove()
    return w, h

def edge_rect(cx, cy, hw, hh, tx, ty):
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx + hw, cy
    sx = hw / abs(dx) if dx else float("inf")
    sy = hh / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s

# ============================================================================
# ГЕНЕРАТОРЫ ДИАГРАММ
# ============================================================================

def draw_class_diagram():
    """Диаграмма классов"""
    fig, ax = plt.subplots(figsize=(14, 10), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    boxes = {}
    for name, (x, y, stereo, attrs, meths) in CLASS_DIAGRAM["classes"].items():
        w, h = 2.5, 2.0
        boxes[name] = {"cx": x, "cy": y, "w": w, "h": h, "attrs": attrs, "meths": meths}
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=CLS_FILL, edgecolor=INK, lw=1.5))
        ax.text(x, y+h/2-0.15, name, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
        ax.plot([x-w/2, x+w/2], [y+h/2-0.35, y+h/2-0.35], color=INK, lw=0.8)
        for i, attr in enumerate(attrs):
            ax.text(x-w/2+0.1, y+h/2-0.45-i*0.2, attr, ha="left", va="top", fontsize=FS_MEM)
        ax.plot([x-w/2, x+w/2], [y+h/2-0.35-len(attrs)*0.2, y+h/2-0.35-len(attrs)*0.2], color=INK, lw=0.8)
        for i, meth in enumerate(meths):
            ax.text(x-w/2+0.1, y-h/2+0.1+i*0.2, meth, ha="left", va="bottom", fontsize=FS_MEM)
    
    for src, dst, kind, cs, cd in CLASS_DIAGRAM["edges"]:
        b1, b2 = boxes[src], boxes[dst]
        p1 = edge_rect(b1["cx"], b1["cy"], b1["w"]/2, b1["h"]/2, b2["cx"], b2["cy"])
        p2 = edge_rect(b2["cx"], b2["cy"], b2["w"]/2, b2["h"]/2, b1["cx"], b1["cy"])
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=LINE_CLR, lw=1.2)
        if kind == "comp":
            ax.plot([p1[0]], [p1[1]], 's', markersize=8, color=INK, fillstyle='full')
    
    ax.set_title("Диаграмма классов: ИС «Мониторинг KPI ТЦ»", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_chen_diagram():
    """Концептуальная диаграмма (Чен)"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    for name, (x, y, attrs, pk, ang) in CHEN_DIAGRAM["entities"].items():
        w, h = 2.0, 1.2
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=ENT_FILL, edgecolor=INK, lw=1.5))
        ax.text(x, y, name, ha="center", va="center", fontsize=FS_NAME, fontweight="bold")
        
        for i, attr in enumerate(attrs):
            ax_ = x + 1.5 * math.cos(math.radians(ang + i*30 - 45))
            ay_ = y + 1.5 * math.sin(math.radians(ang + i*30 - 45))
            ax.add_patch(Ellipse((ax_, ay_), 0.8, 0.5, facecolor=ATT_FILL, edgecolor=INK, lw=1.0))
            ax.text(ax_, ay_, attr, ha="center", va="center", fontsize=FS_ATT)
            ax.plot([x, ax_], [y, ay_], color=LINE_CLR, lw=0.8)
    
    for e1, c1, rname, c2, e2, rx, ry in CHEN_DIAGRAM["relations"]:
        ax.add_patch(Polygon([(rx, ry+0.4), (rx+0.6, ry), (rx, ry-0.4), (rx-0.6, ry)], 
                            facecolor=REL_FILL, edgecolor=INK, lw=1.3))
        ax.text(rx, ry, rname, ha="center", va="center", fontsize=FS_REL)
        ax.text(rx-0.7, ry+0.2, c1, ha="right", va="center", fontsize=FS_CARD, fontweight="bold")
        ax.text(rx+0.7, ry+0.2, c2, ha="left", va="center", fontsize=FS_CARD, fontweight="bold")
    
    ax.set_title("Концептуальная ER-диаграмма (нотация Чена)", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_component_diagram():
    """Диаграмма компонентов"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    for name, (x, y, ctype, ports) in COMPONENT_DIAGRAM["components"].items():
        w, h = 2.5, 1.5
        rect = Rectangle((x-w/2, y-h/2), w, h, facecolor=COMP_FILL, edgecolor=INK, lw=1.5)
        ax.add_patch(rect)
        # Иконка компонента
        ax.plot([x-w/2+0.2, x-w/2+0.2, x-w/2+0.5], [y+h/2-0.2, y+h/2-0.5, y+h/2-0.5], color=INK, lw=1.5)
        ax.text(x, y+h/2-0.15, name, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
        for i, port in enumerate(ports):
            ax.text(x, y-h/2+0.15+i*0.25, port, ha="center", va="bottom", fontsize=FS_MEM)
    
    for src, dst, style in COMPONENT_DIAGRAM["edges"]:
        # Упрощенное соединение
        ax.annotate("", xy=(COMPONENT_DIAGRAM["components"][dst][0], COMPONENT_DIAGRAM["components"][dst][1]),
                   xytext=(COMPONENT_DIAGRAM["components"][src][0], COMPONENT_DIAGRAM["components"][src][1]),
                   arrowprops=dict(arrowstyle="->", color=LINE_CLR, lw=1.2, 
                                  linestyle='--' if style == "dashed" else (':' if style == "dotted" else '-')))
    
    ax.set_title("Диаграмма компонентов", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_deployment_diagram():
    """Диаграмма развертывания"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    for name, (x, y, ntype, specs) in DEPLOYMENT_DIAGRAM["nodes"].items():
        w, h = 3.0, 2.0
        rect = Rectangle((x-w/2, y-h/2), w, h, facecolor=DEPLOY_FILL, edgecolor=INK, lw=1.5, 
                        boxstyle="round,pad=0.3")
        ax.add_patch(rect)
        ax.text(x, y+h/2-0.2, name, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
        for i, spec in enumerate(specs):
            ax.text(x, y-h/2+0.15+i*0.25, spec, ha="center", va="bottom", fontsize=FS_MEM)
    
    for src, dst, label in DEPLOYMENT_DIAGRAM["connections"]:
        sx, sy = DEPLOYMENT_DIAGRAM["nodes"][src][0], DEPLOYMENT_DIAGRAM["nodes"][src][1]
        dx, dy = DEPLOYMENT_DIAGRAM["nodes"][dst][0], DEPLOYMENT_DIAGRAM["nodes"][dst][1]
        ax.annotate("", xy=(dx, dy), xytext=(sx, sy),
                   arrowprops=dict(arrowstyle="<->", color=LINE_CLR, lw=1.2))
        mx, my = (sx+dx)/2, (sy+dy)/2
        ax.text(mx, my+0.15, label, ha="center", va="bottom", fontsize=8, style="italic")
    
    ax.set_title("Диаграмма развертывания", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_sequence_diagram():
    """Диаграмма последовательности"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    lifelines = SEQUENCE_DIAGRAM["lifelines"]
    x_positions = {ll: 2 + i*2.2 for i, ll in enumerate(lifelines)}
    
    # Линии жизни
    for ll in lifelines:
        x = x_positions[ll]
        ax.plot([x, x], [0.5, 12], color=INK, lw=1.0)
        rect = Rectangle((x-0.9, 11.5), 1.8, 0.8, facecolor=CLS_FILL, edgecolor=INK, lw=1.2)
        ax.add_patch(rect)
        ax.text(x, 11.9, ll, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
    
    # Сообщения
    for i, (from_ll, to_ll, msg, mtype) in enumerate(SEQUENCE_DIAGRAM["messages"]):
        from_name = lifelines[from_ll] if isinstance(from_ll, int) else from_ll
        to_name = lifelines[to_ll] if isinstance(to_ll, int) else to_ll
        
        if mtype == "self":
            x = x_positions[from_name]
            y = 11 - i*0.8
            ax.add_patch(Rectangle((x+0.3, y-0.3), 0.6, 0.6, fill=False, edgecolor=INK, lw=1.0))
            ax.text(x+1.2, y, msg, ha="left", va="center", fontsize=9)
        else:
            x1, x2 = x_positions[from_name], x_positions[to_name]
            y = 11 - i*0.8
            ax.annotate("", xy=(x2, y), xytext=(x1, y),
                       arrowprops=dict(arrowstyle="->", color=LINE_CLR, lw=1.2))
            ax.text((x1+x2)/2, y+0.15, msg, ha="center", va="bottom", fontsize=9)
    
    ax.set_ylim(0, 12.5)
    ax.set_xlim(0, len(lifelines)*2.5)
    ax.set_title("Диаграмма последовательности: Запуск системы", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_usecase_diagram(data, title):
    """Диаграмма вариантов использования (универсальная)"""
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    # Актеры
    for actor, (x, y) in data["actors"].items():
        ax.text(x, y+0.6, "👤", ha="center", va="bottom", fontsize=20)
        ax.text(x, y, actor, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
    
    # Варианты использования (овалы)
    for uc, (x, y) in data["usecases"].items():
        ax.add_patch(Ellipse((x, y), 2.0, 1.0, facecolor=ENT_FILL, edgecolor=INK, lw=1.3))
        ax.text(x, y, uc, ha="center", va="center", fontsize=FS_MEM, wrap=True)
    
    # Связи
    for actor, uc, ctype in data["connections"]:
        if actor in data["actors"] and uc in data["usecases"]:
            ax, ay = data["actors"][actor]
            ux, uy = data["usecases"][uc]
            ax.annotate("", xy=(ux, uy), xytext=(ax, ay),
                       arrowprops=dict(arrowstyle="-", color=LINE_CLR, lw=1.2))
    
    # Граница системы
    ax.add_patch(Rectangle((4, 4), 14, 10, fill=False, edgecolor=INK, lw=1.5, linestyle="--"))
    ax.text(11, 13.8, "Система мониторинга KPI", ha="center", va="bottom", fontsize=FS_NAME, style="italic")
    
    ax.set_title(title, fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

# ============================================================================
# GUI ПРИЛОЖЕНИЕ
# ============================================================================
class DiagramGeneratorApp:
    def __init__(self, root):
        self.root = root
        root.title("Генератор UML-диаграмм: ИС «Мониторинг KPI ТЦ»")
        root.geometry("1200x800")
        
        self.fig = None
        self.current_diagram = None
        
        # Панель выбора диаграмм
        panel = ttk.Frame(root, padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(panel, text="Выберите диаграмму:", font=("Arial", 12, "bold")).pack(pady=10)
        
        diagrams = [
            ("1. Диаграмма классов", draw_class_diagram),
            ("2. Концептуальная (Чен)", draw_chen_diagram),
            ("3. Диаграмма компонентов", draw_component_diagram),
            ("4. Диаграмма развертывания", draw_deployment_diagram),
            ("5. Диаграмма последовательности", draw_sequence_diagram),
            ("6. Use Case (Администратор)", lambda: draw_usecase_diagram(USECASE_ADMIN, "Диаграмма вариантов использования: Администратор")),
            ("7. Use Case (Оператор)", lambda: draw_usecase_diagram(USECASE_USER, "Диаграмма вариантов использования: Оператор")),
        ]
        
        for name, func in diagrams:
            btn = ttk.Button(panel, text=name, command=lambda f=func: self.show_diagram(f))
            btn.pack(fill=tk.X, pady=3)
        
        # Кнопки экспорта
        ttk.Label(panel, text="\nЭкспорт:", font=("Arial", 11, "bold")).pack(pady=(20, 10))
        ttk.Button(panel, text=" PNG", command=lambda: self.save("png")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 SVG", command=lambda: self.save("svg")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 PDF", command=lambda: self.save("pdf")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 Все диаграммы", command=self.save_all).pack(fill=tk.X, pady=10)
        
        # Область отображения
        self.plot_frame = ttk.Frame(root)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(self.plot_frame, text="Выберите диаграмму слева для просмотра", 
                 font=("Arial", 14), foreground="gray").pack(expand=True)
        
        # Показать первую диаграмму по умолчанию
        self.show_diagram(draw_class_diagram)
    
    def show_diagram(self, draw_func):
        if self.fig:
            plt.close(self.fig)
        
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        self.fig = draw_func()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
    
    def save(self, fmt):
        if not self.fig:
            messagebox.showwarning("Внимание", "Сначала выберите диаграмму")
            return
        
        types = {"png": [("PNG image", "*.png")], "svg": [("SVG vector", "*.svg")], 
                "pdf": [("PDF document", "*.pdf")]}
        path = filedialog.asksaveasfilename(title=f"Сохранить как {fmt.upper()}",
                   defaultextension=f".{fmt}", filetypes=types[fmt])
        if path:
            try:
                dpi = 200 if fmt == "png" else None
                self.fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight", 
                               facecolor=self.fig.get_facecolor())
                messagebox.showinfo("Готово", f"Сохранено:\n{path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def save_all(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if not folder:
            return
        
        diagrams = [
            ("class_diagram", draw_class_diagram),
            ("chen_er", draw_chen_diagram),
            ("components", draw_component_diagram),
            ("deployment", draw_deployment_diagram),
            ("sequence", draw_sequence_diagram),
            ("usecase_admin", lambda: draw_usecase_diagram(USECASE_ADMIN, "Use Case Admin")),
            ("usecase_user", lambda: draw_usecase_diagram(USECASE_USER, "Use Case User")),
        ]
        
        count = 0
        for name, func in diagrams:
            try:
                fig = func()
                for fmt in ["png", "svg", "pdf"]:
                    path = os.path.join(folder, f"{name}.{fmt}")
                    dpi = 200 if fmt == "png" else None
                    fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight")
                    plt.close(fig)
                count += 1
            except Exception as e:
                print(f"Error saving {name}: {e}")
        
        messagebox.showinfo("Готово", f"Сохранено {count} диаграмм в 3 форматах:\n{folder}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiagramGeneratorApp(root)
    root.mainloop()
# -*- coding: utf-8 -*-
"""
Генератор всех UML-диаграмм для ИС «Мониторинг KPI Торгового Центра».
Экспорт: PNG, SVG, EPS, draw.io (diagrams.net)
Запуск: python -m app.diagrams.generate_all
"""
import os
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

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ============================================================================
# НАСТРОЙКИ ПУТЕЙ
# ============================================================================
DEFAULT_DIR = r"F:\VK_Projects\Mikhail_Barash\2026-10-13_01 - realtime_kpi_monitor\Diagrams"
os.makedirs(DEFAULT_DIR, exist_ok=True)

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
FS_NAME, FS_STEREO, FS_MEM, FS_CARD, FS_TITLE = 11, 8.5, 8.5, 9, 14

# ============================================================================
# ДАННЫЕ ДИАГРАММ (сокращенно для примера, полные данные в коде ниже)
# ============================================================================
CLASS_DIAGRAM = {
    "classes": {
        # Уровень 1: Ядро и конфигурация
        "ConfigManager": (2, 14, "", 
            ["+ config: dict", "+ file_path: str"], 
            ["+ load()", "+ get(key, default)"]),
        "DockerManager": (6, 14, "", 
            ["+ client: DockerClient", "+ containers: dict"], 
            ["+ start_stack()", "+ stop_stack()", "+ wait_for_healthy()"]),
        "DataGenerator": (10, 14, "", 
            ["+ kafka_broker: str", "+ topic: str", "+ running: bool"], 
            ["+ start()", "+ generate_metrics()", "+ stop()"]),
        "StreamProcessor": (14, 14, "", 
            ["+ kafka_broker: str", "+ window_size: int", "+ running: bool"], 
            ["+ process(callback)", "+ aggregate_metrics()", "+ stop()"]),
        
        # Уровень 2: Сервисы и главное окно
        "AlertManager": (2, 10, "", 
            ["+ thresholds: dict", "+ telegram_token: str"], 
            ["+ check_and_alert(metrics)", "+ send_telegram(msg)"]),
        "KPIMonitorGUI": (6, 10, "", 
            ["+ root: CTk", "+ docker_manager: DockerManager", "+ alert_manager: AlertManager"], 
            ["+ _build_header()", "+ _build_tabs()", "+ _toggle_theme()"]),
        "LoginDialog": (10, 10, "", 
            ["+ entry_login: CTkEntry", "+ entry_pass: CTkEntry"], 
            ["+ _build_ui()", "+ _login()"]),
        "ClickHouseClient": (14, 10, "", 
            ["+ host: str", "+ database: str", "+ client: Client"], 
            ["+ query(sql)", "+ insert(data)", "+ ensure_tables()"]),
            
        # Уровень 3: Вкладки интерфейса
        "DashboardTab": (2, 6, "", 
            ["+ kpi_cards: dict", "+ zone_cards: dict"], 
            ["+ _build()", "+ _on_zone_click()"]),
        "AnalyticsTab": (6, 6, "", 
            ["+ period_var: StringVar", "+ metric_var: StringVar", "+ fig: Figure"], 
            ["+ _build()", "+ _update_chart()"]),
        "ZonesTab": (10, 6, "", 
            ["+ tree: Treeview"], 
            ["+ _build()", "+ _show_zone_details()"]),
        "AlertsTab": (14, 6, "", 
            ["+ _build()"], 
            []),
        "InfrastructureTab": (18, 6, "", 
            ["+ _build()"], 
            []),
            
        # Уровень 4: Управление пользователями и настройки
        "UsersTab": (6, 2, "", 
            ["+ users: list", "+ tree: Treeview"], 
            ["+ _build()", "+ _add_user()", "+ _on_user_saved()"]),
        "UserForm": (10, 2, "", 
            ["+ entry_login: CTkEntry", "+ entry_name: CTkEntry", "+ role_var: StringVar"], 
            ["+ _build_ui(user_data)", "+ _save()"]),
        "SettingsTab": (14, 2, "", 
            ["+ _build()"], 
            []),
    },
    "edges": [
        # Конфигурация питает всё
        ("ConfigManager", "DockerManager", "assoc", "1", "1"),
        ("ConfigManager", "AlertManager", "assoc", "1", "1"),
        ("ConfigManager", "StreamProcessor", "assoc", "1", "1"),
        ("ConfigManager", "DataGenerator", "assoc", "1", "1"),
        
        # Ядро обработки
        ("DataGenerator", "StreamProcessor", "assoc", "1", "1"),
        ("StreamProcessor", "AlertManager", "assoc", "1", "1"),
        ("StreamProcessor", "ClickHouseClient", "assoc", "1", "1"),
        ("DockerManager", "ClickHouseClient", "assoc", "1", "1"),
        
        # GUI и его компоненты (Композиция: GUI владеет вкладками)
        ("KPIMonitorGUI", "DockerManager", "aggr", "1", "1"),
        ("KPIMonitorGUI", "AlertManager", "aggr", "1", "1"),
        ("KPIMonitorGUI", "LoginDialog", "assoc", "1", "1"),
        ("KPIMonitorGUI", "DashboardTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "AnalyticsTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "ZonesTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "AlertsTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "InfrastructureTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "UsersTab", "comp", "1", "1"),
        ("KPIMonitorGUI", "SettingsTab", "comp", "1", "1"),
        
        # Связи внутри вкладок
        ("UsersTab", "UserForm", "comp", "1", "*"),
    ]
}

CHEN_DIAGRAM = {
    "entities": {
        "Пользователь": (2, 12, ["id", "login", "role", "name"], 0, 135),
        "Сессия": (2, 8, ["id", "token", "user_id"], 0, 180),
        "Метрика": (7, 12, ["id", "timestamp", "source", "cpu"], 0, 90),
        "Алерт": (12, 12, ["id", "type", "value", "threshold"], 0, 45),
        "ЗонаТЦ": (7, 7, ["id", "name", "capacity"], 0, 270),
        "Событие": (12, 7, ["id", "zone_id", "type"], 0, 315),
    },
    "relations": [
        ("Пользователь", "1", "Имеет", "N", "Сессия", 2, 10),
        ("Пользователь", "1", "Получает", "N", "Алерт", 7, 10),
        ("ЗонаТЦ", "1", "Генерирует", "N", "Метрика", 5, 9.5),
        ("Метрика", "1", "Вызывает", "N", "Алерт", 10, 10),
        ("ЗонаТЦ", "1", "Содержит", "N", "Событие", 9.5, 7),
    ]
}

COMPONENT_DIAGRAM = {
    "components": {
        "DataGenerator": (2, 12, "producer"),
        "Redpanda/Kafka": (6, 12, "broker"),
        "StreamProcessor": (10, 12, "processor"),
        "ClickHouse": (14, 12, "database"),
        "AlertManager": (10, 7, "service"),
        "DockerManager": (2, 7, "orchestrator"),
        "KPIMonitorGUI": (6, 7, "ui"),
    },
    "edges": [
        ("DataGenerator", "Redpanda/Kafka"), ("Redpanda/Kafka", "StreamProcessor"),
        ("StreamProcessor", "ClickHouse"), ("StreamProcessor", "AlertManager"),
        ("DockerManager", "Redpanda/Kafka"), ("DockerManager", "ClickHouse"),
        ("KPIMonitorGUI", "DockerManager"), ("KPIMonitorGUI", "ClickHouse"),
    ]
}

DEPLOYMENT_DIAGRAM = {
    "nodes": {
        "Workstation": (2, 12, "desktop", ["Python 3.11", "GUI"]),
        "Docker: Redpanda": (7, 14, "server", ["Port 9092"]),
        "Docker: ClickHouse": (12, 14, "database", ["Port 8123"]),
        "Docker: Grafana": (17, 14, "monitoring", ["Port 3000"]),
        "Telegram API": (17, 7, "cloud", ["HTTPS"]),
    },
    "connections": [
        ("Workstation", "Docker: Redpanda"), ("Workstation", "Docker: ClickHouse"),
        ("Docker: Redpanda", "Docker: ClickHouse"), ("Docker: Redpanda", "Telegram API"),
    ]
}

SEQUENCE_DIAGRAM = {
    "lifelines": ["User", "GUI", "DockerMgr", "Redpanda", "ClickHouse", "Processor"],
    "messages": [
        (0, 1, "1. Ввести логин/пароль"), (1, 2, "2. start_stack()"),
        (2, 3, "3. docker run"), (2, 4, "4. docker run"),
        (2, 5, "5. ensure_tables()"), (1, 5, "6. process()"),
        (5, 3, "7. Consume"), (5, 4, "8. INSERT"),
    ]
}

USECASE_ADMIN = {
    "actors": {"Администратор": (1, 10)},
    "usecases": {
        "Авторизоваться": (5, 13), "Просматривать Dashboard": (9, 13),
        "Управлять пользователями": (13, 13), "Настраивать алерты": (17, 13),
        "Просматривать аналитику": (9, 9), "Мониторить зоны ТЦ": (13, 9),
    },
    "connections": [
        ("Администратор", "Авторизоваться"), ("Администратор", "Просматривать Dashboard"),
        ("Администратор", "Управлять пользователями"), ("Администратор", "Настраивать алерты"),
        ("Администратор", "Просматривать аналитику"), ("Администратор", "Мониторить зоны ТЦ"),
    ]
}

USECASE_USER = {
    "actors": {"Оператор": (1, 10)},
    "usecases": {
        "Авторизоваться": (5, 13), "Просматривать Dashboard": (9, 13),
        "Просматривать аналитику": (13, 13), "Мониторить зоны ТЦ": (17, 13),
        "Получать алерты": (9, 9), "Просматривать детали зон": (13, 9),
    },
    "connections": [
        ("Оператор", "Авторизоваться"), ("Оператор", "Просматривать Dashboard"),
        ("Оператор", "Просматривать аналитику"), ("Оператор", "Мониторить зоны ТЦ"),
        ("Оператор", "Получать алерты"), ("Оператор", "Просматривать детали зон"),
    ]
}

DIAGRAMS_META = [
    ("1. Диаграмма классов", "class_diagram", "class"),
    ("2. Концептуальная (Чен)", "chen_er", "chen"),
    ("3. Диаграмма компонентов", "components", "generic"),
    ("4. Диаграмма развертывания", "deployment", "generic"),
    ("5. Диаграмма последовательности", "sequence", "generic"),
    ("6. Use Case (Администратор)", "usecase_admin", "generic"),
    ("7. Use Case (Оператор)", "usecase_user", "generic"),
]

# ============================================================================
# УТИЛИТЫ
# ============================================================================
def measure(ax, fig, label, fs):
    
    t = ax.text(0, 0, label, fontsize=fs, ha="center", va="center")
    try:
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
        w, h = bb.width / fig.dpi, bb.height / fig.dpi
    except Exception:
        w, h = len(label) * 0.62 * fs / 72.0, 1.25 * fs / 72.0
    t.remove()
    return w, h

def edge_rect(cx, cy, hw, hh, tx, ty):
    """Вычисляет точку пересечения линии с границей прямоугольника."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx + hw, cy
    sx = hw / abs(dx) if dx else float("inf")
    sy = hh / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s

def _esc(s):
    return html.escape(str(s), quote=True)

# ============================================================================
# ЭКСПОРТ В DRAW.IO (Специализированный для Class и Chen)
# ============================================================================
def export_class_drawio(path):
    scale, margin = 70.0, 30.0
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<mxfile host="app.diagrams.net" version="24.0.0">',
         '  <diagram id="cls1" name="Classes">', '    <mxGraphModel>', '      <root>',
         '        <mxCell id="0"/>', '        <mxCell id="1" parent="0"/>']
    
    for name, (x, y, stereo, attrs, meths) in CLASS_DIAGRAM["classes"].items():
        w, h = 2.5, 2.0
        gx, gy = (x - w/2) * scale + margin, (16 - (y + h/2)) * scale + margin # инверсия Y для drawio
        head = (f"&lt;&lt;{stereo}&gt;&gt;&lt;br&gt;" if stereo else "") + f"<b>{name}</b>"
        attrs_html = "<br>".join(f"<u>{a}</u>" if a.startswith("+ id") or a.startswith("id ") else a for a in attrs)
        meths_html = "<br>".join(meths)
        value = _esc(head + ("<hr>" + attrs_html if attrs else "") + ("<hr>" + meths_html if meths else ""))
        style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#E8F4FC;strokeColor=#1A1A1A;strokeWidth=1.5;fontSize=9;align=left;spacingLeft=6;verticalAlign=top;"
        L.append(f'        <mxCell id="C_{name}" value="{value}" style="{style}" vertex="1" parent="1"><mxGeometry x="{gx:.1f}" y="{gy:.1f}" width="{w*scale:.1f}" height="{h*scale:.1f}" as="geometry"/></mxCell>')
    
    for src, dst, kind, cs, cd in CLASS_DIAGRAM["edges"]:
        st = "endArrow=open;endFill=0;" if kind == "assoc" else "endArrow=diamondThin;endFill=1;"
        L.append(f'        <mxCell id="e_{src}_{dst}" value="" style="{st}html=1;strokeColor=#444444;strokeWidth=1.3;" edge="1" parent="1" source="C_{src}" target="C_{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    
    L += ['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>']
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

def export_chen_drawio(path):
    scale, margin = 90.0, 30.0
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<mxfile host="app.diagrams.net" version="24.0.0">',
         '  <diagram id="chen1" name="Chen ER">', '    <mxGraphModel>', '      <root>',
         '        <mxCell id="0"/>', '        <mxCell id="1" parent="0"/>']
    
    ent_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#DCEBFB;strokeColor=#1A1A1A;strokeWidth=1.5;fontSize=11;fontStyle=1;"
    rel_style = "rhombus;whiteSpace=wrap;html=1;fillColor=#FCE4D6;strokeColor=#1A1A1A;strokeWidth=1.3;fontSize=9;"
    att_style = "ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1A1A1A;strokeWidth=1.1;fontSize=9;"
    
    for name, (x, y, attrs, pk, ang) in CHEN_DIAGRAM["entities"].items():
        w, h = 2.0, 1.2
        gx, gy = (x - w/2) * scale + margin, (16 - (y + h/2)) * scale + margin
        L.append(f'        <mxCell id="E_{name}" value="{_esc(name)}" style="{ent_style}" vertex="1" parent="1"><mxGeometry x="{gx:.1f}" y="{gy:.1f}" width="{w*scale:.1f}" height="{h*scale:.1f}" as="geometry"/></mxCell>')
        for i, attr in enumerate(attrs):
            ax_ = x + 1.5 * math.cos(math.radians(ang + i*30 - 45))
            ay_ = y + 1.5 * math.sin(math.radians(ang + i*30 - 45))
            aw, ah = 0.8, 0.5
            agx, agy = (ax_ - aw/2) * scale + margin, (16 - (ay_ + ah/2)) * scale + margin
            st = att_style + "fontStyle=4;" if i == pk else att_style
            L.append(f'        <mxCell id="A_{name}_{i}" value="{_esc(attr)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{agx:.1f}" y="{agy:.1f}" width="{aw*scale:.1f}" height="{ah*scale:.1f}" as="geometry"/></mxCell>')
            L.append(f'        <mxCell id="ea_{name}_{i}" value="" style="endArrow=none;html=1;strokeColor=#555555;strokeWidth=1;" edge="1" parent="1" source="E_{name}" target="A_{name}_{i}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    
    for i, (e1, c1, rname, c2, e2, rx, ry) in enumerate(CHEN_DIAGRAM["relations"]):
        rw, rh = 1.2, 0.8
        rgx, rgy = (rx - rw/2) * scale + margin, (16 - (ry + rh/2)) * scale + margin
        L.append(f'        <mxCell id="R_{i}" value="{_esc(rname)}" style="{rel_style}" vertex="1" parent="1"><mxGeometry x="{rgx:.1f}" y="{rgy:.1f}" width="{rw*scale:.1f}" height="{rh*scale:.1f}" as="geometry"/></mxCell>')
        edge_st = "endArrow=none;html=1;strokeColor=#1A1A1A;strokeWidth=1.3;fontSize=9;fontStyle=1;"
        L.append(f'        <mxCell id="R_{i}_a" value="{_esc(c1)}" style="{edge_st}" edge="1" parent="1" source="E_{e1}" target="R_{i}"><mxGeometry relative="1" as="geometry"/></mxCell>')
        L.append(f'        <mxCell id="R_{i}_b" value="{_esc(c2)}" style="{edge_st}" edge="1" parent="1" source="R_{i}" target="E_{e2}"><mxGeometry relative="1" as="geometry"/></mxCell>')

    L += ['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>']
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

def export_generic_drawio(fig, path):
    """Универсальный экспорт для остальных диаграмм через считывание matplotlib patches"""
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<mxfile host="app.diagrams.net" version="24.0.0">',
         '  <diagram id="gen1" name="Generic">', '    <mxGraphModel>', '      <root>',
         '        <mxCell id="0"/>', '        <mxCell id="1" parent="0"/>']
    
    ax = fig.axes[0]
    scale, margin = 100.0, 50.0
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    
    # Экспорт текстов
    for i, text in enumerate(ax.texts):
        pos = text.get_position()
        # Преобразование координат данных в координаты draw.io
        gx = (pos[0] / 20.0) * scale + margin 
        gy = height * scale - (pos[1] / 15.0) * scale + margin
        
        style = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;"
        val = _esc(text.get_text())
        L.append(f'        <mxCell id="txt_{i}" value="{val}" style="{style}" vertex="1" parent="1"><mxGeometry x="{gx:.1f}" y="{gy:.1f}" width="120" height="30" as="geometry"/></mxCell>')
    
    # Экспорт прямоугольников (приближенно)
    for i, patch in enumerate(ax.patches):
        if isinstance(patch, Rectangle):
            xy = patch.get_xy()
            w, h = patch.get_width(), patch.get_height()
            gx = (xy[0] / 20.0) * scale + margin
            gy = height * scale - ((xy[1] + h) / 15.0) * scale + margin
            gw, gh = (w / 20.0) * scale, (h / 15.0) * scale
            
            fc = patch.get_facecolor()
            fc_hex = '#%02x%02x%02x' % (int(fc[0]*255), int(fc[1]*255), int(fc[2]*255)) if len(fc) >= 3 else "#FFFFFF"
            
            style = f"rounded=0;whiteSpace=wrap;html=1;fillColor={fc_hex};strokeColor=#1A1A1A;strokeWidth=1.5;"
            L.append(f'        <mxCell id="rect_{i}" value="" style="{style}" vertex="1" parent="1"><mxGeometry x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" as="geometry"/></mxCell>')

    L += ['      </root>', '    </mxGraphModel>', '  </diagram>', '</mxfile>']
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

# ============================================================================
# ГЕНЕРАТОРЫ ДИАГРАММ (упрощенные для компактности, но рабочие)
# ============================================================================
def draw_class_diagram():
    """Диаграмма классов (полная, 15 классов)"""
    # Увеличили figsize до 18x12, чтобы вместить все 15 классов
    fig, ax = plt.subplots(figsize=(18, 12), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig)
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    ax.axis("off")
    
    boxes = {}
    for name, (x, y, stereo, attrs, meths) in CLASS_DIAGRAM["classes"].items():
        w, h = 2.8, 2.2 # Чуть увеличили размер блоков
        boxes[name] = {"cx": x, "cy": y, "w": w, "h": h, "attrs": attrs, "meths": meths}
        
        # Рисуем прямоугольник класса
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=CLS_FILL, edgecolor=INK, lw=1.5))
        
        # Имя класса
        ax.text(x, y+h/2-0.15, name, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
        ax.plot([x-w/2, x+w/2], [y+h/2-0.35, y+h/2-0.35], color=INK, lw=0.8)
        
        # Атрибуты
        for i, attr in enumerate(attrs):
            is_pk = attr.startswith("id ") or attr.startswith("+ id")
            ax.text(x-w/2+0.1, y+h/2-0.45-i*0.2, attr, ha="left", va="top", fontsize=FS_MEM)
            if is_pk: # Подчеркивание первичного ключа (если есть)
                tw = len(attr) * 0.62 * FS_MEM / 72.0
                ax.plot([x-w/2+0.1, x-w/2+0.1+tw], [y+h/2-0.45-i*0.2-0.05, y+h/2-0.45-i*0.2-0.05], color=INK, lw=0.8)
                
        # Разделитель методов
        if attrs:
            ax.plot([x-w/2, x+w/2], [y+h/2-0.35-len(attrs)*0.2, y+h/2-0.35-len(attrs)*0.2], color=INK, lw=0.8)
            
        # Методы
        for i, meth in enumerate(meths):
            ax.text(x-w/2+0.1, y-h/2+0.1+i*0.2, meth, ha="left", va="bottom", fontsize=FS_MEM)
    
    # Рисуем связи
    for src, dst, kind, cs, cd in CLASS_DIAGRAM["edges"]:
        b1, b2 = boxes[src], boxes[dst]
        
        # Вычисляем точки на границах прямоугольников
        p1 = edge_rect(b1["cx"], b1["cy"], b1["w"]/2, b1["h"]/2, b2["cx"], b2["cy"])
        p2 = edge_rect(b2["cx"], b2["cy"], b2["w"]/2, b2["h"]/2, b1["cx"], b1["cy"])
        
        # Стиль линии
        ls = "solid"
        if kind == "aggr":
            ax.plot([p1[0]], [p1[1]], 'D', markersize=7, color=INK, fillstyle='full', markerfacecolor='white')
        elif kind == "comp":
            ax.plot([p1[0]], [p1[1]], 'D', markersize=7, color=INK, fillstyle='full')
            
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=LINE_CLR, lw=1.2, linestyle=ls)
        
        # Кратности (если нужны, можно раскомментировать)
        # ax.text(p1[0]+0.2, p1[1]+0.2, cs, fontsize=FS_CARD, color=INK)
        # ax.text(p2[0]-0.2, p2[1]-0.2, cd, fontsize=FS_CARD, color=INK)
    
    ax.set_title("Диаграмма классов: ИС «Мониторинг KPI ТЦ» (15 классов)", fontsize=FS_TITLE, fontweight="bold", pad=10)
    
    # Автоматически подстраиваем границы холста под все блоки
    all_x = [b["cx"] - b["w"]/2 - 1 for b in boxes.values()] + [b["cx"] + b["w"]/2 + 1 for b in boxes.values()]
    all_y = [b["cy"] - b["h"]/2 - 1 for b in boxes.values()] + [b["cy"] + b["h"]/2 + 1 for b in boxes.values()]
    ax.set_xlim(min(all_x), max(all_x))
    ax.set_ylim(min(all_y), max(all_y))
    
    return fig

def draw_chen_diagram():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    for name, (x, y, attrs, pk, ang) in CHEN_DIAGRAM["entities"].items():
        w, h = 2.0, 1.2
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=ENT_FILL, edgecolor=INK, lw=1.5))
        ax.text(x, y, name, ha="center", va="center", fontsize=FS_NAME, fontweight="bold")
        for i, attr in enumerate(attrs):
            ax_, ay_ = x + 1.5*math.cos(math.radians(ang+i*30-45)), y + 1.5*math.sin(math.radians(ang+i*30-45))
            ax.add_patch(Ellipse((ax_, ay_), 0.8, 0.5, facecolor=ATT_FILL, edgecolor=INK, lw=1.0))
            ax.text(ax_, ay_, attr, ha="center", va="center", fontsize=FS_ATT)
            ax.plot([x, ax_], [y, ay_], color=LINE_CLR, lw=0.8)
    for e1, c1, rname, c2, e2, rx, ry in CHEN_DIAGRAM["relations"]:
        ax.add_patch(Polygon([(rx, ry+0.4), (rx+0.6, ry), (rx, ry-0.4), (rx-0.6, ry)], facecolor=REL_FILL, edgecolor=INK, lw=1.3))
        ax.text(rx, ry, rname, ha="center", va="center", fontsize=FS_REL)
    ax.set_title("Концептуальная ER-диаграмма (нотация Чена)", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_component_diagram():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    for name, (x, y, ctype) in COMPONENT_DIAGRAM["components"].items():
        w, h = 2.5, 1.5
        ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.1", facecolor=COMP_FILL, edgecolor=INK, lw=1.5))
        ax.text(x, y, name, ha="center", va="center", fontsize=FS_NAME, fontweight="bold")
    for src, dst in COMPONENT_DIAGRAM["edges"]:
        ax.annotate("", xy=COMPONENT_DIAGRAM["components"][dst][:2], xytext=COMPONENT_DIAGRAM["components"][src][:2],
                   arrowprops=dict(arrowstyle="->", color=LINE_CLR, lw=1.2))
    ax.set_title("Диаграмма компонентов", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_deployment_diagram():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    for name, (x, y, ntype, specs) in DEPLOYMENT_DIAGRAM["nodes"].items():
        w, h = 3.0, 2.0
        ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=DEPLOY_FILL, edgecolor=INK, lw=1.5, boxstyle="round,pad=0.3"))
        ax.text(x, y+h/2-0.2, name, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
        for i, spec in enumerate(specs): ax.text(x, y-h/2+0.15+i*0.25, spec, ha="center", va="bottom", fontsize=FS_MEM)
    for src, dst in DEPLOYMENT_DIAGRAM["connections"]:
        ax.annotate("", xy=DEPLOYMENT_DIAGRAM["nodes"][dst][:2], xytext=DEPLOYMENT_DIAGRAM["nodes"][src][:2],
                   arrowprops=dict(arrowstyle="<->", color=LINE_CLR, lw=1.2))
    ax.set_title("Диаграмма развертывания", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_sequence_diagram():
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    lifelines = SEQUENCE_DIAGRAM["lifelines"]
    x_pos = {ll: 2 + i*2.2 for i, ll in enumerate(lifelines)}
    for ll in lifelines:
        x = x_pos[ll]
        ax.plot([x, x], [0.5, 12], color=INK, lw=1.0)
        ax.add_patch(Rectangle((x-0.9, 11.5), 1.8, 0.8, facecolor=CLS_FILL, edgecolor=INK, lw=1.2))
        ax.text(x, 11.9, ll, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
    for i, (from_ll, to_ll, msg) in enumerate(SEQUENCE_DIAGRAM["messages"]):
        x1, x2 = x_pos[lifelines[from_ll]], x_pos[lifelines[to_ll]]
        y = 11 - i*0.8
        ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="->", color=LINE_CLR, lw=1.2))
        ax.text((x1+x2)/2, y+0.15, msg, ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 12.5); ax.set_xlim(0, len(lifelines)*2.5)
    ax.set_title("Диаграмма последовательности: Запуск системы", fontsize=FS_TITLE, fontweight="bold", pad=10)
    return fig

def draw_usecase_diagram(data, title):
    fig, ax = plt.subplots(figsize=(14, 9), dpi=DPI_WIN)
    fig.canvas = FigureCanvasAgg(fig); fig.patch.set_facecolor(BG); ax.set_facecolor(BG); ax.axis("off")
    for actor, (x, y) in data["actors"].items():
        ax.text(x, y+0.6, "👤", ha="center", va="bottom", fontsize=20)
        ax.text(x, y, actor, ha="center", va="top", fontsize=FS_NAME, fontweight="bold")
    for uc, (x, y) in data["usecases"].items():
        ax.add_patch(Ellipse((x, y), 2.0, 1.0, facecolor=ENT_FILL, edgecolor=INK, lw=1.3))
        ax.text(x, y, uc, ha="center", va="center", fontsize=FS_MEM, wrap=True)
    for actor, uc in data["connections"]:
        ax, ay = data["actors"][actor]; ux, uy = data["usecases"][uc]
        ax.annotate("", xy=(ux, uy), xytext=(ax, ay), arrowprops=dict(arrowstyle="-", color=LINE_CLR, lw=1.2))
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
        self.current_name = None
        self.current_draw_func = None
        
        panel = ttk.Frame(root, padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(panel, text="Выберите диаграмму:", font=("Arial", 12, "bold")).pack(pady=10)
        
        for label, name, dtype in DIAGRAMS_META:
            btn = ttk.Button(panel, text=label, command=lambda n=name, d=dtype: self.show_diagram(n, d))
            btn.pack(fill=tk.X, pady=3)
        
        ttk.Label(panel, text="\nЭкспорт:", font=("Arial", 11, "bold")).pack(pady=(20, 10))
        ttk.Button(panel, text="💾 PNG", command=lambda: self.save("png")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 SVG", command=lambda: self.save("svg")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 EPS", command=lambda: self.save("eps")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="💾 draw.io", command=lambda: self.save("drawio")).pack(fill=tk.X, pady=2)
        ttk.Button(panel, text="📁 Сохранить ВСЕ", command=self.save_all).pack(fill=tk.X, pady=15)
        
        self.plot_frame = ttk.Frame(root)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.show_diagram("class_diagram", "class")

    def show_diagram(self, name, dtype):
        self.current_name = name
        self.current_dtype = dtype
        
        if self.fig: plt.close(self.fig)
        for widget in self.plot_frame.winfo_children(): widget.destroy()
        
        if name == "class_diagram": self.current_draw_func = draw_class_diagram
        elif name == "chen_er": self.current_draw_func = draw_chen_diagram
        elif name == "components": self.current_draw_func = draw_component_diagram
        elif name == "deployment": self.current_draw_func = draw_deployment_diagram
        elif name == "sequence": self.current_draw_func = draw_sequence_diagram
        elif name == "usecase_admin": self.current_draw_func = lambda: draw_usecase_diagram(USECASE_ADMIN, "Диаграмма вариантов использования: Администратор")
        elif name == "usecase_user": self.current_draw_func = lambda: draw_usecase_diagram(USECASE_USER, "Диаграмма вариантов использования: Оператор")
        
        self.fig = self.current_draw_func()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, self.plot_frame).update()

    def save(self, fmt):
        if not self.current_name: return
        
        default_path = os.path.join(DEFAULT_DIR, f"{self.current_name}.{fmt}")
        ext_map = {"png": "PNG image", "svg": "SVG vector", "eps": "Encapsulated PostScript", "drawio": "draw.io diagram"}
        
        path = filedialog.asksaveasfilename(
            title=f"Сохранить как {fmt.upper()}",
            defaultextension=f".{fmt}",
            filetypes=[(ext_map.get(fmt, "All files"), f"*.{fmt}")],
            initialdir=DEFAULT_DIR,
            initialfile=f"{self.current_name}.{fmt}"
        )
        if not path: return
        
        try:
            if fmt == "drawio":
                if self.current_name == "class_diagram":
                    export_class_drawio(path)
                elif self.current_name == "chen_er":
                    export_chen_drawio(path)
                else:
                    export_generic_drawio(self.fig, path)
            else:
                dpi = 300 if fmt == "png" else None
                self.fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight", facecolor=self.fig.get_facecolor())
            messagebox.showinfo("Готово", f"Сохранено:\n{path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_all(self):
        if not messagebox.askyesno("Подтверждение", f"Сохранить все 7 диаграмм в 4 форматах (28 файлов) в папку:\n{DEFAULT_DIR}?"):
            return
        
        count = 0
        for label, name, dtype in DIAGRAMS_META:
            try:
                fig = self._get_draw_func(name, dtype)()
                for fmt in ["png", "svg", "eps", "drawio"]:
                    path = os.path.join(DEFAULT_DIR, f"{name}.{fmt}")
                    if fmt == "drawio":
                        if name == "class_diagram": export_class_drawio(path)
                        elif name == "chen_er": export_chen_drawio(path)
                        else: export_generic_drawio(fig, path)
                    else:
                        dpi = 300 if fmt == "png" else None
                        fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
                    count += 1
                plt.close(fig)
            except Exception as e:
                print(f"Error saving {name}: {e}")
        
        messagebox.showinfo("Готово", f"Успешно сохранено {count} файлов в папку:\n{DEFAULT_DIR}")

    def _get_draw_func(self, name, dtype):
        if name == "class_diagram": return draw_class_diagram
        if name == "chen_er": return draw_chen_diagram
        if name == "components": return draw_component_diagram
        if name == "deployment": return draw_deployment_diagram
        if name == "sequence": return draw_sequence_diagram
        if name == "usecase_admin": return lambda: draw_usecase_diagram(USECASE_ADMIN, "Admin")
        if name == "usecase_user": return lambda: draw_usecase_diagram(USECASE_USER, "User")
        return draw_class_diagram

if __name__ == "__main__":
    root = tk.Tk()
    app = DiagramGeneratorApp(root)
    root.mainloop()
# sidebar.py
from dash import html
import dash_bootstrap_components as dbc
from flask_login import current_user

from database.db_conn import SessionLocal
# from services.MosaicMed import dashboard_chef, dashboard_patient, short_name_mo
from services.MosaicMed.flaskapp.models import RoleModuleAccess
from services.MosaicMed.pages.admin.settings import get_setting
SIDEBAR_CONTENT_STYLE_HIDE_SCROLL = {
    "overflow-y": "scroll",
    "height": "calc(100% - 60px)",
    "padding": "0rem 1px 30px",
    "scrollbar-width": "none",
    "::-webkit-scrollbar": {
        "width": "0px"
    },
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": "56px",
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "background-color": "#f8f9fa",
    "transition": "all 0.2s",
    "display": "flex",
    "flex-direction": "column",
}


def fetch_role_access(role):
    session = SessionLocal()
    access_data = session.query(RoleModuleAccess).filter_by(role=role).all()
    session.close()
    return [access.module for access in access_data]


def get_sidebar():
    nav_items = [
        dbc.NavLink([html.I(className="fas fa-home"), html.Span(" Главная", className="nav-text", title="Главная")],
                    href="/main", active="exact", className="nav-item", id="nav-home"),
    ]

    if current_user.is_authenticated:
        modules = fetch_role_access(current_user.role)
        if 'doctors-report' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("По врачу", href="/doctors-report/doctor"),
                    dbc.DropdownMenuItem("Список врачей", href="/doctors-report/list-doctors"),
                ],
                label=[html.I(className="fas fa-user-md"),
                       html.Span(" Врач", className="nav-text", title="Диспансерный учет")],
                nav=True,
                id="nav-doctors-report",
                right=True,
            ))
        if 'dispensary' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Взрослые", href="/dispensary/adult"),
                    dbc.DropdownMenuItem("Дети", href="/dispensary/children"),
                    dbc.DropdownMenuItem("Репродуктивное", href="/dispensary/reproductive"),
                ],
                label=[html.I(className="fas fa-stethoscope"),
                       html.Span(" Диспансеризация", className="nav-text", title="Диспансеризация")],
                nav=True,
                id="nav-dispensary",
                right=True,
            ))
        if 'dispensary-observation' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Взрослые", href="/dispensary-observation/adult"),
                    dbc.DropdownMenuItem("ИСЗЛ", href="/dispensary-observation/iszl"),
                ],
                label=[html.I(className="fas fa-notes-medical"),
                       html.Span(" Диспансерное наблюдение", className="nav-text", title="Диспансерный учет")],
                nav=True,
                id="nav-dispensary",
                right=True,
            ))
        if 'econ' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Сверхподушевик", href="/econ/sv-pod"),
                    dbc.DropdownMenuItem("Объемные показатели", href="/econ/report"),
                    dbc.DropdownMenuItem("ПГГ", href="/econ/pgg"),
                    dbc.DropdownMenuItem("По врачам", href="/econ/by-doctor"),
                    dbc.DropdownMenuItem("По врачам оплаченные", href="/econ/by-doctor-cel"),
                    dbc.DropdownMenuItem("По врачам диспансеризация", href="/econ/by-doctor-dispensary"),
                    dbc.DropdownMenuItem("Новые территории", href="/econ/new-territories"),
                    dbc.DropdownMenuItem("Маршруты ПН1", href="/econ/route-children"),
                    dbc.DropdownMenuItem("Диспансеризация по возрастам", href="/econ/disp"),
                    dbc.DropdownMenuItem("Стационары", href="/econ/stationary"),
                ],
                label=[html.I(className="fas fa-dollar-sign"),
                       html.Span(" Экономические отчеты", className="nav-text", title="Экономические отчеты")],
                nav=True,
                id="nav-econ",
                right=True,
            ))
        if 'volumes' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Талоны", href="/volumes/target"),
                    dbc.DropdownMenuItem("Финансы", href="/volumes/finance"),
                ],
                label=[html.I(className="fas fa-chart-line"),
                       html.Span(" Объемные показатели", className="nav-text", title="Объемы")],
                nav=True,
                id="nav-volumes",
                right=True,
            ))
        if 'it' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Для сборки счетов", href="/it/gen-invoices"),
                    dbc.DropdownMenuItem("Обновление базы данных", href="/it/update-bd"),
                    dbc.DropdownMenuItem("Месяцы по статусам", href="/it/stat-months"),
                    dbc.DropdownMenuItem("Месяцы по смо", href="/it/for-smo"),
                    dbc.DropdownMenuItem("Цель 3", href="/it/cel3"),
                    dbc.DropdownMenuItem("Сохранить файлы", href="/it/files_loader"),
                ],
                label=[html.I(className="fas fa-desktop"),
                       html.Span(" IT отдел", className="nav-text", title="IT отдел")],
                nav=True,
                id="nav-it",
                right=True,
            ))
        if 'admin' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Пользователи", href="/admin/users"),
                    dbc.DropdownMenuItem("Роли", href="/admin/roles"),
                    dbc.DropdownMenuItem("Настройки", href="/admin/settings"),
                ],
                label=[html.I(className="fas fa-user-cog"),
                       html.Span(" Админпанель", className="nav-text", title="Админпанель")],
                nav=True,
                id="nav-admin",
                right=True,
            ))
        if 'iszl' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Диспансерное наблюдение", href="/iszl/disp-nab"),
                    dbc.DropdownMenuItem("Население", href="/iszl/people"),
                ],
                label=[html.I(className="fas fa-heartbeat"),
                       html.Span(" ИСЗЛ", className="nav-text", title="ИСЗЛ")],
                nav=True,
                id="nav-iszl",
                right=True,
            ))
        if 'other-reports' in modules:
            nav_items.append(dbc.NavLink([html.I(className="fas fa-chart-bar"),
                                          html.Span(" Другие отчеты", className="nav-text", title="Другие отчеты")],
                                         href="/other-reports", active="exact", className="nav-item",
                                         id="nav-other-reports"))
        if 'eln' in modules:
            nav_items.append(dbc.NavLink(
                [html.I(className="fas fa-file-medical"), html.Span(" ЭЛН", className="nav-text", title="ЭЛН")],
                href="/eln", active="exact", className="nav-item", id="nav-eln"))
        if 'filling-lists' in modules:
            nav_items.append(dbc.NavLink([html.I(className="fas fa-edit"),
                                          html.Span(" Заполнение списков", className="nav-text",
                                                    title="Заполнение списков")],
                                         href="/filling-lists", active="exact", className="nav-item",
                                         id="nav-filling-lists"))
        if 'wo-coupons' in modules:
            nav_items.append(dbc.NavLink([html.I(className="fas fa-list-alt"),
                                          html.Span(" Талоны WEB-ОМС", className="nav-text", title="Талоны WEB-ОМС")],
                                         href="/wo-coupons", active="exact", className="nav-item", id="nav-wo-coupons"))
        if 'dashboards' in modules:
            nav_items.append(dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem("Главный врач", href="/dashboard/chef"),
                    dbc.DropdownMenuItem("Пациенты", href="/dashboard/patient")
                ],
                label=[html.I(className="fas fa-tachometer-alt"),
                       html.Span(" Дашборды", className="nav-text", title="Дашборды")],
                nav=True,
                id="nav-dashboards",
                right=True,
            ))

    sidebar_content = dbc.Nav(nav_items, vertical=True, pills=True)

    return html.Div(
        [
            html.H2(get_setting("short_name_mo"), className="display-8 text-center", id="sidebar-title"),
            html.Hr(style={"margin": "1px"}),
            html.Div(sidebar_content, style=SIDEBAR_CONTENT_STYLE_HIDE_SCROLL)
        ],
        id="sidebar",
        style=SIDEBAR_STYLE,
    )

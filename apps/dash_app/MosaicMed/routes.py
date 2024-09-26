from dash import html, dcc

from services.MosaicMed.callback.redirect_href import dashboard_chef_layout
from services.MosaicMed.pages.WO_coupons.status_talon.tab import app_tabs_talon_wo
from services.MosaicMed.pages.admin.settings import settings_layout
from services.MosaicMed.pages.admin.users import users_layout
from services.MosaicMed.pages.admin.roles import roles_layout
from services.MosaicMed.pages.dispensary.adults.tab import app_tabs_da
from services.MosaicMed.pages.dispensary.children.tab import app_tabs_dc
from services.MosaicMed.pages.dispensary.reproductive.tab import app_tabs_reproductive
from services.MosaicMed.pages.doctors_talon.doctor.tab import app_tabs_doctors
from services.MosaicMed.pages.doctors_talon.doctors_list.tab import app_tabs_doctors_list
from services.MosaicMed.pages.economic_reports.by_doctors.tab import app_tabs_by_doctor
from services.MosaicMed.pages.economic_reports.by_doctors_cel.tab import app_tabs_by_doctor_cel
from services.MosaicMed.pages.economic_reports.by_doctors_dispensary.tab import app_tabs_by_doctor_dispensary
from services.MosaicMed.pages.economic_reports.dispensary_price.dispensary_price import tab_layout_dispensary_price
from services.MosaicMed.pages.economic_reports.new_territories.tab import new_territories
from services.MosaicMed.pages.economic_reports.reports.tab import app_tabs_econ_reports
from services.MosaicMed.pages.economic_reports.route_children_dd.route_children_dd import tab_layout_route_children
from services.MosaicMed.pages.economic_reports.stationary.tab import stationary
from services.MosaicMed.pages.economic_reports.sv_pod.sv_pod import tab_layout_sv_pod
from services.MosaicMed.pages.economic_reports.volumes_indicators.volumes_indicators import app_pgg_amb
from services.MosaicMed.pages.eln.tab import app_tabs_eln
from services.MosaicMed.pages.filling_lists.tab import app_tabs_fil_list
from services.MosaicMed.pages.iszl.disp_nabl.tab import app_tabs_iszl_disp_nab
from services.MosaicMed.pages.iszl.people.tab import app_tabs_people_iszl
from services.MosaicMed.pages.it_department.cel_3.tab import app_tabs_cel3
from services.MosaicMed.pages.it_department.for_smo.for_smo import tab_layout_for_smo
from services.MosaicMed.pages.it_department.generation_invoices.generation_invoices import tab_layout_other_gen_invoices
from services.MosaicMed.pages.it_department.status_months.status_months import tab_layout_other_stat_months
from services.MosaicMed.pages.it_department.update_database.update_database import tab_layout_it_update_bd
from services.MosaicMed.pages.other_reports.tab import app_tabs_other_reports

# Проверка доступа для специфичных маршрутов
routes = {
    "/doctors-report/doctor": app_tabs_doctors,
    "/doctors-report/list-doctors": app_tabs_doctors_list,
    "/dispensary/adult": app_tabs_da,
    "/dispensary/children": app_tabs_dc,
    "/dispensary/reproductive": app_tabs_reproductive,
    "/econ/sv-pod": tab_layout_sv_pod,
    "/econ/report": app_tabs_econ_reports,
    "/econ/pgg": app_pgg_amb,
    "/econ/by-doctor": app_tabs_by_doctor,
    "/econ/by-doctor-cel": app_tabs_by_doctor_cel,
    "/econ/by-doctor-dispensary": app_tabs_by_doctor_dispensary,
    "/econ/new-territories": new_territories,
    "/econ/route-children": tab_layout_route_children,
    "/econ/disp": tab_layout_dispensary_price,
    "/econ/stationary": stationary,
    "/it/gen-invoices": tab_layout_other_gen_invoices,
    "/it/update-bd": tab_layout_it_update_bd,
    "/it/stat-months": tab_layout_other_stat_months,
    "/it/for-smo": tab_layout_for_smo,
    "/it/cel3": app_tabs_cel3,
    "/it/files_loader": html.Div(dcc.Location(href="/it/files_loader", id='dashboard-chef-redirect')),
    "/admin/users": users_layout,
    "/admin/roles": roles_layout(),
    "/admin/settings": settings_layout,
    "/iszl/disp-nab": app_tabs_iszl_disp_nab,
    "/iszl/people": app_tabs_people_iszl,
    "/dispensary-observation/adult": html.H2("Взрослые"),
    "/dispensary-observation/children": html.H2("Дети"),
    "/dispensary-observation/iszl": app_tabs_iszl_disp_nab,
    "/other-reports": app_tabs_other_reports,
    "/eln": app_tabs_eln,
    "/volumes/target": html.H2("Талоны"),
    "/volumes/finance": html.H2("Финансы"),
    "/filling-lists": app_tabs_fil_list,
    "/wo-coupons": app_tabs_talon_wo,
    "/dashboard/chef": dashboard_chef_layout,
    "/dashboard/patient": html.H2("Пациент"),
}

from services.MosaicMed.pages.admin.settings import get_setting
from dash import dcc, html

dashboard_chef_url = get_setting("dashboard_chef")

dashboard_chef_layout = html.Div(dcc.Location(href=dashboard_chef_url, id='dashboard-chef-redirect'))

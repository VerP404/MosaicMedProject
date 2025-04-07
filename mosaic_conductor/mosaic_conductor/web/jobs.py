import os
from dagster import job, graph, in_process_executor
from mosaic_conductor.mosaic_conductor.web.opps.wo_start import open_site_op
from mosaic_conductor.mosaic_conductor.web.opps.wo_filter import search_text_op
from mosaic_conductor.mosaic_conductor.web.selenium_driver import selenium_driver_resource


@graph
def google_search_graph():
    site_url = open_site_op()
    search_text_op(site_url)  # Передаём результат open_site_op во второй op


google_search_job = google_search_graph.to_job(
    resource_defs={"selenium_driver": selenium_driver_resource},
    config={
        "resources": {
            "selenium_driver": {
                "config": {
                    "browser": "chrome",
                    "destination_folder": os.path.join(os.getcwd(), "downloads"),
                    "target_url": "https://www.google.com"
                }
            }
        }
    },
    executor_def=in_process_executor,
)

import os
import base64
import datetime
import pytz
import logging

from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud.logging_v2.services.logging_service_v2 import LoggingServiceV2Client
from google.cloud.logging_v2.types import ListLogEntriesRequest
from openpyxl import Workbook

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route("/", methods=["POST"])
def log_report_generator():
    try:
        envelope = request.get_json()
        if not envelope:
            return "Bad Request: no JSON body", 400

        pubsub_message = envelope.get('message')
        if not pubsub_message:
            return "Bad Request: no message in JSON", 400

        data = pubsub_message.get('data')
        if data:
            decoded_data = base64.b64decode(data).decode('utf-8')
            logging.info(f"Pub/Sub message data: {decoded_data}")

        generate_log_report()
        return jsonify({"status": "Report generated"}), 200

    except Exception as e:
        logging.exception("Error during request")
        return jsonify({"error": str(e)}), 500


def generate_log_report():
    PROJECT_ID = "adept-chemist-465510-p3"
    BUCKET_NAME = "helloworlddemo13"

    est = pytz.timezone("US/Eastern")
    now_est = datetime.datetime.now(est)

    # ✅ Set END time to today's 5:00 AM EST
    end_est = est.localize(datetime.datetime(now_est.year, now_est.month, now_est.day, 5, 0, 0))
    
    # ✅ Set START time to yesterday's 5:00 AM EST
    start_est = end_est - datetime.timedelta(days=1)

    start_utc = start_est.astimezone(pytz.utc)
    end_utc = end_est.astimezone(pytz.utc)

    start_time_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time_str = end_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Create log filter string
    log_filter = f"""
        resource.type="k8s_container"
        resource.labels.project_id="{PROJECT_ID}"
        resource.labels.location="us-central1"
        resource.labels.cluster_name="autopilot-cluster-1"
        resource.labels.namespace_name="default"
        labels.k8s-pod/app="hello-server"
        severity>=DEFAULT
        timestamp >= "{start_time_str}"
        timestamp < "{end_time_str}"
    """

    # ✅ Use RPC client from low-level LoggingServiceV2Client
    logging_client = LoggingServiceV2Client()
    request = ListLogEntriesRequest(
        resource_names=[f"projects/{PROJECT_ID}"],
        filter=log_filter,
    )

    entries = logging_client.list_log_entries(request=request)

    # Group log entries by hour
    hourly_counts = {}
    hourly_counts = {}
    for entry in entries:
        ts = entry.timestamp.astimezone(est)  # No .ToDatetime()
        hour_key = ts.replace(minute=0, second=0, microsecond=0)
        hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1


    # Create Excel report
    wb = Workbook()
    ws = wb.active
    ws.title = "Hourly Log Count"
    ws.append(["Hour (EST)", "Log Count"])

    for hour in sorted(hourly_counts):
        ws.append([hour.strftime("%Y-%m-%d %H:%M:%S"), hourly_counts[hour]])

    file_name = f"log_report_{start_est.strftime('%Y%m%d')}.xlsx"
    local_path = f"/tmp/{file_name}"
    wb.save(local_path)

    # Upload to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_filename(local_path)

    logging.info(f"Uploaded report to gs://{BUCKET_NAME}/{file_name}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

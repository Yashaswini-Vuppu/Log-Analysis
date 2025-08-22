🚀 Automating GKE Log Analysis with Cloud Run Functions, Cloud Logging, Pub/Sub, and Cloud Scheduler



Ever wondered how to automate log analysis for your Kubernetes workloads and get hourly insights delivered straight to Cloud Storage?

 That’s exactly what I built recently using Google Cloud’s serverless and observability tools!



🔹 The Challenge

In our GKE Autopilot cluster, we needed to:

1. Run a daily job at 5:00 AM EST.

2. Query Google Cloud Logging for Kubernetes container logs.

3. Aggregate log entries per hour from 5:00 AM EST → next day 5:00 AM EST.

4. Export the results into an Excel file.

5. Store the file in a Cloud Storage bucket for easy access and reporting.



🔹 The Architecture

Here’s the end-to-end flow:



1. Cloud Scheduler → triggers a Pub/Sub topic at 5:00 AM EST daily.

2. Pub/Sub Topic → receives the trigger message.

3. Cloud Run Functions Service → subscribed to the Pub/Sub topic.

When triggered, the Cloud Run Function service:

4. Cloud Logging Query → fetches and filters logs based on filter:



resource.type="k8s_container"

resource.labels.project_id="your_project_id"

resource.labels.location="your_cluster_location"

resource.labels.cluster_name="your_cluster_name"

resource.labels.namespace_name="default"

labels.k8s-pod/app="your_pod_name"

severity>=DEFAULT



5. Data Processing → counts log entries grouped by hour.

6. Excel Export → results are written to a .xlsx file.



🔹 Implementation Steps

1. Create a Pub/Sub Topic

gcloud pubsub topics create daily-logging-job

2. Schedule the Job

Since Cloud Scheduler runs in UTC, we adjust for 5 AM EST (~10 AM UTC).

gcloud scheduler jobs create pubsub daily-logging-trigger \

  --schedule "0 10 * * *" \

  --topic daily-logging-job \

  --message-body "{}"

3. Deploy Cloud Run Functions Service

a. Connect the service to the Pub/Sub topic.

b. Grant the service account these roles:

    roles/logging.viewer

    roles/storage.objectAdmin

4. Python Service Code (Core Logic)

The Cloud Run Functions does the following:

a. Receives Pub/Sub messages.

b. Defines the 5 AM EST → next day 5 AM EST window.

c. Queries Cloud Logging using the Python client library.

d. Groups logs per hour.

e. Writes results to Excel (pandas + openpyxl).

f. Uploads the file to Cloud Storage.



 🔹The Result

✨ Every morning, a new Excel report is generated and stored in Cloud Storage.

The report provides a clear hourly breakdown of log activity, which is invaluable for:

1. Identifying peak traffic times.

2. Spotting unusual error spikes.

3. Sharing log summaries with non-technical stakeholders.

4. Detecting spikes or anomalies quickly.



By combining these services, we created a fully automated, cost-efficient, and maintainable log reporting system.



💬 What other automations would you like to see with Cloud Logging? Let’s discuss!



🔖 #GoogleCloud #CloudRun #CloudLogging #GKE #Automation #Python #DevOps #CloudScheduler #Observability #Kubernetes #Serverless

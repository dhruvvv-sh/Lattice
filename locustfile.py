from locust import HttpUser, task, between
import uuid

class StorageUser(HttpUser):

    wait_time = between(0.2, 1)

    @task(6)
    def list_objects(self):
        self.client.get("/objects/")

    @task(2)
    def list_buckets(self):
        self.client.get("/buckets/")

    @task(1)
    def download_object(self):
        self.client.get("/objects/1")

    @task(1)
    def upload(self):
        filename = f"{uuid.uuid4()}.pdf"

        with open("Sample.pdf", "rb") as f:
            self.client.post(
                "/objects/upload/1",
                files={
                    "file": (filename, f, "application/pdf")
                }
            )
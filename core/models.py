from django.contrib.auth.models import User
from django.db import models

from .helpers import extract_text_from_pdf


class Session(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Document(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    file = models.FileField(upload_to="documents/")
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def extract_and_save_text(self):
        if not self.extracted_text:
            self.extracted_text = extract_text_from_pdf(self.file.path)
            self.save()


class Query(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    asked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

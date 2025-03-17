from django.contrib.auth.models import User
from django.db import models

from .constants import SessionTypeEnum


class Session(models.Model):
    session_type = models.CharField(
        max_length=255,
        choices=SessionTypeEnum.choices(),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Document(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    extracted_text = models.TextField(blank=True, null=True)
    text_chunks = models.JSONField(default=list, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class DocumentEmbedding(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="embeddings")
    chunk_index = models.IntegerField()
    embedding = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("document", "chunk_index")


class Query(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    asked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

    def save(self, *args, **kwargs):
        if not self.answer:
            raise ValueError("You must provide an answer")
        super().save(*args, **kwargs)

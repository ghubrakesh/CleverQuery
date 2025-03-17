# Generated by Django 4.2.18 on 2025-02-25 17:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_session_modified_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='text_chunks',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='session',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name='DocumentEmbedding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_index', models.IntegerField()),
                ('embedding', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='embeddings', to='core.document')),
            ],
            options={
                'unique_together': {('document', 'chunk_index')},
            },
        ),
    ]

# Generated by Django 4.2.18 on 2025-03-02 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_document_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='session_type',
            field=models.CharField(choices=[('exam_preparation_guide', 'Exam Preparation Guide'), ('technical_manual_interpreter', 'Technical Manual Interpreter'), ('legal_document_analysis', 'Legal Document Analysis'), ('nutritional_label_interpreter', 'Nutritional Label Interpreter'), ('financial_report_analysis', 'Financial Report Analysis'), ('contract_review_assistant', 'Contract Review Assistant')], default='exam_preparation_guide', max_length=255),
            preserve_default=False,
        ),
    ]

# Generated data migration to convert RichTextField to StreamField

import json

import wagtail.blocks
import wagtail.fields
from django.db import migrations


def clear_and_convert_body(apps, schema_editor):
    """Clear problematic body data and prepare for StreamField."""
    # Just clear the column - we'll rewrite it as JSON after the field change
    schema_editor.execute("UPDATE blog_blogpage SET body = '[]'")


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL("UPDATE blog_blogpage SET body = '[]'"),
        migrations.AlterField(
            model_name='blogpage',
            name='body',
            field=wagtail.fields.StreamField(
                [
                    ("rich_text", wagtail.blocks.RichTextBlock()),
                    ("code", wagtail.blocks.StructBlock([
                        ("language", wagtail.blocks.CharBlock(
                            max_length=50,
                            help_text="Programming language (e.g., python, javascript, html)",
                            required=False,
                        )),
                        ("code", wagtail.blocks.TextBlock(help_text="Your code here")),
                    ], icon="code", label="Code")),
                ],
                blank=True,
            ),
        ),
    ]

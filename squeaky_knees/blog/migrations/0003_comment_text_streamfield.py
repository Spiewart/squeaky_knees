import wagtail.fields
from django.db import migrations


def clear_comment_text(apps, schema_editor):
    """Clear comment text before migration to StreamField."""
    Comment = apps.get_model("blog", "Comment")
    Comment.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_alter_blogpage_body"),
    ]

    operations = [
        migrations.RunPython(clear_comment_text),
        migrations.AlterField(
            model_name="comment",
            name="text",
            field=wagtail.fields.StreamField(
                [("rich_text", 0), ("code", 3)],
                block_lookup={
                    0: ("wagtail.blocks.RichTextBlock", (), {}),
                    1: (
                        "wagtail.blocks.CharBlock",
                        (),
                        {
                            "help_text": "Programming language (e.g., python, javascript, html)",
                            "max_length": 50,
                            "required": False,
                        },
                    ),
                    2: (
                        "wagtail.blocks.TextBlock",
                        (),
                        {"help_text": "Your code here"},
                    ),
                    3: (
                        "wagtail.blocks.StructBlock",
                        [[("language", 1), ("code", 2)]],
                        {},
                    ),
                },
            ),
        ),
    ]

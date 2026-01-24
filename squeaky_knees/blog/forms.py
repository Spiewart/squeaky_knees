from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    """Form for submitting comments on blog posts."""

    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Leave a comment...",
                },
            ),
        }
        labels = {
            "text": "Your Comment",
        }

"""Search form for blog posts."""

from django import forms


class BlogSearchForm(forms.Form):
    """Form for searching blog posts."""

    query = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search blog posts...",
                "class": "form-control",
                "autocomplete": "off",
            },
        ),
    )

    def clean_query(self):
        """Validate and clean search query."""
        query = self.cleaned_data.get("query", "").strip()

        if not query:
            msg = "Search query cannot be empty."
            raise forms.ValidationError(msg)

        if len(query) < 2:
            msg = "Search query must be at least 2 characters."
            raise forms.ValidationError(msg)

        if len(query) > 200:
            msg = "Search query cannot exceed 200 characters."
            raise forms.ValidationError(msg)

        # Remove potentially harmful characters
        return query.replace("<", "").replace(">", "").replace('"', "").replace("'", "")

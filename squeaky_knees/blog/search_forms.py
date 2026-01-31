"""Search form for blog posts."""

from django import forms

from config.validation import validate_username


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
            }
        ),
    )

    def clean_query(self):
        """Validate and clean search query."""
        query = self.cleaned_data.get("query", "").strip()

        if not query:
            raise forms.ValidationError("Search query cannot be empty.")

        if len(query) < 2:
            raise forms.ValidationError("Search query must be at least 2 characters.")

        if len(query) > 200:
            raise forms.ValidationError("Search query cannot exceed 200 characters.")

        # Remove potentially harmful characters
        query = query.replace("<", "").replace(">", "").replace('"', "").replace("'", "")

        return query

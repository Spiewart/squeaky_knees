# Django Forms with ReCAPTCHA v3 and Crispy Forms

## Overview

This document explains how to properly integrate Django forms with `django-recaptcha` v3 widget and `crispy-forms` to ensure form submissions work correctly.

## The Problem

When using `django-recaptcha` with the `ReCaptchaV3` widget alongside `crispy-forms`, a common issue occurs where form submissions fail silently:

1. **Button clicks don't trigger submit**: Clicking the submit button produces no console errors and no network requests
2. **Form doesn't respond**: The page appears frozen, nothing happens

### Root Cause

The issue stems from how `crispy-forms` renders forms:

- **`{% crispy form %}`** renders a **complete** `<form>` element including opening `<form>` and closing `</form>` tags
- If you place a submit button **after** `{% crispy form %}`, the button is rendered **outside** the form element
- The ReCAPTCHA v3 widget attaches a submit event listener to the form element
- Submit buttons outside the form don't trigger the form's submit event
- **Result**: Clicking the button does nothing

### Why It Fails Silently

- No JavaScript errors appear because the code is technically correct
- The ReCAPTCHA widget JS loads successfully
- The event listener is properly attached to the form
- The button just isn't inside the form, so clicks never reach the listener

## The Solution

Use `FormHelper` with `form_tag=False` to prevent crispy-forms from rendering `<form>` tags, then manually add them in the template with the button inside.

### Implementation Steps

#### Step 1: Configure FormHelper in Form Class

In your form class (e.g., `squeaky_knees/users/forms.py`):

```python
from allauth.account.forms import SignupForm
from crispy_forms.helper import FormHelper
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3


class UserSignupForm(SignupForm):
    """
    Form for user signup with reCAPTCHA v3 protection.

    Uses FormHelper with form_tag=False to allow manual form tag placement
    in templates, ensuring submit buttons are inside the form element.
    """

    captcha = ReCaptchaField(
        widget=ReCaptchaV3(attrs={"data-action": "signup"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure FormHelper to NOT render <form> tags
        self.helper = FormHelper()
        self.helper.form_tag = False  # Critical setting
```

**Key Points:**

- Import `FormHelper` from `crispy_forms.helper`
- Create `self.helper` in `__init__` method (called when form is instantiated)
- Set `self.helper.form_tag = False` to prevent crispy from rendering form tags
- This setting tells crispy to render **only the fields** (inputs, labels, errors)

#### Step 2: Update Template with Manual Form Tags

In your template (e.g., `squeaky_knees/templates/account/signup.html`):

```django
{% extends "base.html" %}
{% load i18n crispy_forms_tags %}

{% block content %}
  <div class="container mt-4">
    <div class="row">
      <div class="col-lg-6 mx-auto">
        <h1>{% translate "Sign Up" %}</h1>

        {{ form.media }}  {# CRITICAL: Renders reCAPTCHA widget JavaScript #}

        <form method="post" action="{% url 'account_signup' %}">
          {% csrf_token %}

          {% if redirect_field_value %}
            <input type="hidden"
                   name="{{ redirect_field_name }}"
                   value="{{ redirect_field_value }}" />
          {% endif %}

          {% crispy form %}  {# Renders only fields, no <form> tags #}

          <button type="submit" class="btn btn-primary">
            {% translate "Sign Up" %}
          </button>
        </form>
      </div>
    </div>
  </div>
{% endblock content %}
```

**Key Template Elements:**

1. **`{{ form.media }}`**:
   - **MUST** be included to render the JavaScript required by `ReCaptchaV3` widget
   - Without this, the reCAPTCHA widget won't initialize
   - Place it before the `<form>` element

2. **Manual `<form>` tags**:
   - You control the form wrapper
   - Ensures submit button is inside the form element
   - Include `method="post"` and `action="..."`

3. **`{% csrf_token %}`**:
   - Required for Django form submission security
   - Must be inside `<form>` tags

4. **`{% crispy form %}`**:
   - Because `form_tag=False`, this renders **only the fields**
   - No `<form>` or `</form>` tags are generated

5. **Submit button**:
   - Placed **inside** the `</form>` closing tag
   - This is the critical fix - button must be in the form

## How It Works

### Without FormHelper Configuration (Broken)

```django
{# Template #}
{{ form.media }}
{% crispy form %}  {# Renders <form>...fields...</form> #}
<button type="submit">Submit</button>  {# OUTSIDE form element! #}
```

**DOM Structure:**
```html
<script src="recaptcha-widget.js"></script>
<form method="post" action="/signup/">
  <input name="username" />
  <input name="password" />
  <!-- Form ends here -->
</form>
<!-- Button is outside the form -->
<button type="submit">Submit</button>
```

**Result**: Button clicks never trigger the form's submit event. ❌

### With FormHelper Configuration (Working)

```django
{# Template #}
{{ form.media }}
<form method="post" action="/signup/">
  {% csrf_token %}
  {% crispy form %}  {# form_tag=False: renders only fields #}
  <button type="submit">Submit</button>  {# INSIDE form #}
</form>
```

**DOM Structure:**
```html
<script src="recaptcha-widget.js"></script>
<form method="post" action="/signup/">
  <input name="csrfmiddlewaretoken" value="..." />
  <input name="username" />
  <input name="password" />
  <input name="g-recaptcha-response" />
  <!-- Button is inside the form -->
  <button type="submit">Submit</button>
</form>
```

**Result**: Button clicks trigger submit event, reCAPTCHA validates, form submits. ✅

## Verification

### Browser DevTools Check

Open browser console and run:

```javascript
const form = document.querySelector('form');
const button = document.querySelector('button[type="submit"]');
console.log(form.contains(button));  // Should return true
```

**Expected Results:**

- ✅ **`true`**: Button is inside form (correct)
- ❌ **`false`**: Button is outside form (broken)

### Check Event Listeners

```javascript
getEventListeners(document.querySelector('form'));
```

You should see a `submit` listener attached by the reCAPTCHA widget.

## Common Mistakes

### ❌ Mistake 1: Missing form.media

```django
{# BAD: No form.media #}
<form method="post">
  {% crispy form %}
  <button type="submit">Submit</button>
</form>
```

**Problem**: ReCAPTCHA widget JavaScript never loads. Form may appear to work but reCAPTCHA validation is bypassed.

### ❌ Mistake 2: Not Setting form_tag=False

```python
# BAD: No FormHelper configuration
class UserSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3())
    # Missing: self.helper = FormHelper()
    # Missing: self.helper.form_tag = False
```

```django
{# Template ends up with nested forms or button outside #}
{{ form.media }}
{% crispy form %}  {# Renders complete form #}
<button>Submit</button>  {# Outside the form #}
```

**Problem**: Button is outside the form element.

### ❌ Mistake 3: Forgetting CSRF Token

```django
{# BAD: Missing csrf_token #}
{{ form.media }}
<form method="post">
  {% crispy form %}
  <button type="submit">Submit</button>
</form>
```

**Problem**: Django rejects the submission with a 403 CSRF error.

### ✅ Complete Correct Pattern

**Form (forms.py):**
```python
from crispy_forms.helper import FormHelper
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

class MyForm(Form):
    captcha = ReCaptchaField(widget=ReCaptchaV3())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
```

**Template:**
```django
{% load crispy_forms_tags %}

{{ form.media }}
<form method="post" action="{% url 'my_view' %}">
  {% csrf_token %}
  {% crispy form %}
  <button type="submit" class="btn btn-primary">Submit</button>
</form>
```

## Additional Notes

### When to Use This Pattern

Use `FormHelper` with `form_tag=False` when:

1. Using `django-recaptcha` with any widget (especially v3)
2. Need to place buttons or other elements inside the form after crispy rendering
3. Want full control over form element attributes (class, id, action, method)
4. Working with multiple forms on one page

### Alternative: Don't Use Crispy for Submit Button

Another approach is to let crispy render the form completely and use JavaScript to move the button:

```django
{% crispy form %}  {# Renders complete form #}
<button type="submit" id="my-button">Submit</button>

<script>
// Move button inside form
document.querySelector('form').appendChild(
  document.getElementById('my-button')
);
</script>
```

**However**, this approach is:
- More fragile (depends on timing)
- Harder to maintain
- May cause layout shifts
- **Not recommended**

The `FormHelper` approach is cleaner and more reliable.

## Related Files

- **Form Classes**: `squeaky_knees/users/forms.py`
- **Templates**:
  - `squeaky_knees/templates/account/signup.html`
  - `squeaky_knees/templates/socialaccount/signup.html`
- **ReCAPTCHA Configuration**: `config/settings/base.py`
- **Widget Template**: `.venv/lib/.../django_recaptcha/templates/django_recaptcha/includes/js_v3.html`

## Testing

### Current Test Coverage

Comprehensive unit tests verify that all reCAPTCHA forms are correctly configured and work properly in both Django and template layers.

#### Signup Forms Tests (`tests/test_signup_forms.py`)

Files tested:
- `squeaky_knees/templates/account/signup.html`
- `squeaky_knees/templates/socialaccount/signup.html`
- `squeaky_knees/users/forms.py` (UserSignupForm, UserSocialSignupForm)

Test classes and coverage:

1. **SignupFormSubmissionTest** (5 tests)
   - Form page renders successfully
   - All required fields present (CSRF, reCAPTCHA, button)
   - `{{ form.media }}` is rendered (critical for reCAPTCHA widget JS)
   - POST requests work with valid data
   - POST without CSRF token is rejected (security)

2. **SignupTemplateStructureTest** (5 tests)
   - ✅ **Button is inside `<form>` element** (critical fix)
   - ✅ **Only one `<form>` tag exists** (verifies `form_tag=False`)
   - ✅ **CSRF token inside form**
   - ✅ **reCAPTCHA input inside form**
   - ✅ **Form has correct method and action**

3. **SocialSignupFormTest** (1 test)
   - Social signup button placement verified

4. **FormHelperConfigurationTest** (3 tests)
   - ✅ VERIFY `UserSignupForm.helper.form_tag = False`
   - ✅ VERIFY `UserSocialSignupForm.helper.form_tag = False`
   - Verify reCAPTCHA field is present and correct type

**Run signup tests:**
```bash
uv run python manage.py test tests.test_signup_forms
```

#### Comment Form Tests (`tests/test_comment_forms.py`)

Files tested:
- `squeaky_knees/templates/blog/blog_page.html`
- `squeaky_knees/blog/forms.py` (CommentForm)

Test classes and coverage:

1. **CommentFormConfigurationTest** (3 tests)
   - ✅ CommentForm has FormHelper configured
   - ✅ `form_tag=False` is set
   - ✅ reCAPTCHA field is present and correct type
   - ✅ Rate limit constants are configured

2. **CommentFormValidationTest** (4 tests)
   - Comment text validation
   - Rejection of empty comments
   - JSON StreamField input handling
   - Form initialization with/without request

3. **BlogCommentTemplateStructureTest** (6 tests)
   - Blog page renders correctly
   - Comment form section exists
   - ✅ **Comment submit button is inside form element**
   - ✅ `form.media` is rendered
   - ✅ CSRF token is present
   - Authentication requirements enforced

4. **CommentFormSubmissionTest** (3 tests)
   - Unauthenticated user access control
   - Authenticated user form access
   - Request parameter passing to form

5. **RateLimitingTest** (3 tests)
   - Rate limit configuration verified (10 comments/hour)
   - Rate limit constants correct
   - Rate limiting check in validation

**Run comment form tests:**
```bash
uv run python manage.py test tests.test_comment_forms
```

#### Run All Form Tests

```bash
# Run all form-related tests
uv run python manage.py test tests.test_signup_forms tests.test_comment_forms tests.test_recaptcha_forms_integration -v 2

# Run with coverage
uv run coverage run --source='squeaky_knees' manage.py test tests.test_signup_forms tests.test_comment_forms tests.test_recaptcha_forms_integration
uv run coverage report
```

#### Integration Tests (`tests/test_recaptcha_forms_integration.py`)

These tests verify that ALL reCAPTCHA forms in the project follow consistent patterns:

1. **ReCaptchaFormConsistencyTest** (5 tests)
   - ✅ All forms have FormHelper with `form_tag=False`
   - ✅ All forms have ReCaptchaField
   - ✅ All forms use ReCaptchaV3 widget
   - ✅ Signup forms have rate limiting configured
   - ✅ Comment form has rate limiting configured

2. **ReCaptchaDataActionTest** (3 tests)
   - ✅ UserSignupForm uses 'signup' action
   - ✅ UserSocialSignupForm uses 'social_signup' action
   - ✅ CommentForm uses 'comments' action

3. **FormHelperLayoutTest** (2 tests)
   - ✅ All forms have helper layout configured
   - ✅ Layouts include reCAPTCHA field

**Run integration tests:**
```bash
uv run python manage.py test tests.test_recaptcha_forms_integration -v 2
```

### Forms Using ReCAPTCHA

This project uses `django-recaptcha` with the v3 widget (invisible challenge) on:

| Form | Location | Tests |
|------|----------|-------|
| UserSignupForm | `squeaky_knees/users/forms.py` | ✅ test_signup_forms.py |
| UserSocialSignupForm | `squeaky_knees/users/forms.py` | ✅ test_signup_forms.py |
| CommentForm | `squeaky_knees/blog/forms.py` | ✅ test_comment_forms.py |

All forms use:
- `ReCaptchaV3` widget for invisible validation
- `FormHelper` with `form_tag=False` for proper button placement
- Rate limiting to prevent spam/abuse

### Key Tests to Understand

1. **`test_button_is_inside_form_element`**
   - Regex extracts form HTML and verifies button is inside
   - Prevents regression if button placement changes
   - Would fail immediately if FormHelper.form_tag is removed

2. **`test_crispy_form_renders_without_form_tags`**
   - Counts `<form>` tags to verify FormHelper is working
   - Ensures only one `<form>` element (the manual one)
   - Would catch if someone forgets `form_tag=False`

3. **`test_comment_form_button_inside_form`**
   - Verifies comment form button placement on blog page
   - Tests actual template rendering, not just form configuration
   - Ensures fix applies to all forms using CommentForm

### TODO: Selenium End-to-End Tests

**Status**: Not yet implemented

**Description**: Add browser automation tests using Selenium to verify:
- reCAPTCHA JavaScript initializes in real browser
- Form event listeners attach correctly
- Submit button clicks trigger form submission
- Form processes requests in real browser environment (Chrome/Firefox)
- Form submission works with JavaScript enabled and disabled

**Benefits**:
- Tests actual browser behavior, not just HTML structure
- Catches JavaScript timing issues
- Verifies reCAPTCHA widget behavior
- More comprehensive than unit tests

**Implementation**:
- Use `selenium` package for browser automation
- Create `tests/test_signup_forms_e2e.py` for end-to-end tests
- May require `chromedriver` or `geckodriver` setup
- Tests should include:
  - Fill form and click button
  - Verify form submission via network inspection
  - Test with/without reCAPTCHA responses
  - Test error handling

**Notes**:
- Selenium tests are slower than unit tests (real browser startup)
- Consider running separately from main test suite
- Can use `pytest-django` with `pytest-selenium` plugin
- May require Docker container with browser for CI/CD

## References

- [django-recaptcha Documentation](https://github.com/torchbox/django-recaptcha)
- [crispy-forms FormHelper](https://django-crispy-forms.readthedocs.io/en/latest/form_helper.html)
- [Google reCAPTCHA v3](https://developers.google.com/recaptcha/docs/v3)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [pytest-selenium Plugin](https://pytest-selenium.readthedocs.io/)

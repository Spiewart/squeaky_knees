import pytest

from squeaky_knees.blog.models import Comment


@pytest.mark.django_db
class TestBlogModels:
    """Tests for blog models."""

    def test_blog_index_page_creation(self, blog_index):
        """Test blog index page is created."""
        assert blog_index.title == "Blog"
        assert blog_index.live

    def test_blog_page_creation(self, blog_post):
        """Test blog page is created."""
        assert blog_post.title == "Test Blog Post"
        assert blog_post.intro == "This is a test blog post"
        assert blog_post.live

    def test_blog_page_get_context(self, blog_post, client):
        """Test blog page context includes comments."""
        context = blog_post.get_context({})
        assert "comments" in context
        assert "comment_form" in context

    def test_blog_index_page_get_context_with_posts(self, blog_index, blog_post):
        """Test blog index page context includes blog posts."""
        context = blog_index.get_context({})
        assert "blogpages" in context
        blogpages = list(context["blogpages"])
        assert len(blogpages) == 1
        assert blogpages[0].title == "Test Blog Post"

    def test_blog_index_page_get_context_ordered_by_date(self, blog_index):
        """Test blog posts are ordered by date (newest first)."""
        from datetime import date
        from datetime import timedelta

        from squeaky_knees.blog.models import BlogPage

        # Create older post
        older_post = BlogPage(
            title="Older Post",
            date=date.today() - timedelta(days=5),
            intro="Older post",
            slug="older-post",
        )
        older_post.body = [{"type": "rich_text", "value": "<p>Older content</p>"}]
        blog_index.add_child(instance=older_post)
        older_post.save_revision().publish()

        # Create newer post
        newer_post = BlogPage(
            title="Newer Post",
            date=date.today(),
            intro="Newer post",
            slug="newer-post",
        )
        newer_post.body = [{"type": "rich_text", "value": "<p>Newer content</p>"}]
        blog_index.add_child(instance=newer_post)
        newer_post.save_revision().publish()

        context = blog_index.get_context({})
        blogpages = list(context["blogpages"])
        assert len(blogpages) == 2
        assert blogpages[0].title == "Newer Post"
        assert blogpages[1].title == "Older Post"


@pytest.mark.django_db
class TestCommentModel:
    """Tests for comment model."""

    def test_comment_creation(self, blog_post, user):
        """Test comment creation."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )
        assert comment.blog_page == blog_post
        assert comment.author == user
        assert len(comment.text) == 1
        assert not comment.approved  # Should not be approved by default

    def test_comment_str(self, blog_post, user):
        """Test comment string representation."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Test comment</p>"}],
        )
        expected = f"Comment by {user.username} on {blog_post.title}"
        assert str(comment) == expected

    def test_approved_comments_filter(self, blog_post, user):
        """Test filtering approved comments."""
        # Create approved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Approved comment</p>"}],
            approved=True,
        )
        # Create unapproved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Unapproved comment</p>"}],
            approved=False,
        )

        approved_comments = Comment.objects.filter(
            blog_page=blog_post,
            approved=True,
        )
        assert approved_comments.count() == 1

    def test_comments_ordered_by_created(self, blog_post, user):
        """Test comments are ordered by creation date."""
        from datetime import timedelta

        from django.utils import timezone

        # Create older comment
        older_comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Older comment</p>"}],
            approved=True,
        )
        older_comment.created = timezone.now() - timedelta(hours=2)
        older_comment.save()

        # Create newer comment
        newer_comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Newer comment</p>"}],
            approved=True,
        )

        comments = Comment.objects.filter(blog_page=blog_post).order_by("created")
        assert list(comments) == [older_comment, newer_comment]

    def test_blog_page_context_only_shows_approved_comments(self, blog_post, user):
        """Test blog page context only includes approved comments."""
        # Create approved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Approved comment</p>"}],
            approved=True,
        )
        # Create unapproved comment
        Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[{"type": "rich_text", "value": "<p>Unapproved comment</p>"}],
            approved=False,
        )

        context = blog_post.get_context({})
        comments = context["comments"]
        assert comments.count() == 1

    def test_comment_code_block_storage(self, blog_post, user):
        """Test comments can store code blocks in StreamField."""
        comment = Comment.objects.create(
            blog_page=blog_post,
            author=user,
            text=[
                {
                    "type": "code",
                    "value": {"language": "python", "code": "print('ok')"},
                },
            ],
            approved=True,
        )
        assert comment.text[0].block_type == "code"


@pytest.mark.django_db
class TestCodeBlock:
    """Tests for CodeBlock functionality."""

    def test_code_block_creation(self, blog_index, admin_user):
        """Test code block can be created and stored."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        blog_post = BlogPage(
            title="Code Block Test",
            date=date.today(),
            intro="Test code block",
            slug="code-block-test",
        )
        # Set body with code block
        blog_post.body = [
            {
                "type": "code",
                "value": {
                    "language": "python",
                    "code": "def hello():\n    print('Hello, World!')",
                },
            }
        ]
        blog_index.add_child(instance=blog_post)
        blog_post.save_revision().publish()

        # Verify code block was saved
        assert len(blog_post.body) == 1
        assert blog_post.body[0].block_type == "code"
        assert blog_post.body[0].value["language"] == "python"

    def test_mixed_blocks_in_body(self, blog_index, admin_user):
        """Test mixing rich_text and code blocks."""
        from datetime import date

        from squeaky_knees.blog.models import BlogPage

        blog_post = BlogPage(
            title="Mixed Blocks Test",
            date=date.today(),
            intro="Test mixed blocks",
            slug="mixed-blocks-test",
        )
        # Set body with both rich_text and code blocks
        blog_post.body = [
            {
                "type": "rich_text",
                "value": "<p>Here's some code:</p>",
            },
            {
                "type": "code",
                "value": {
                    "language": "javascript",
                    "code": "console.log('Hello');",
                },
            },
            {
                "type": "rich_text",
                "value": "<p>End of code example</p>",
            },
        ]
        blog_index.add_child(instance=blog_post)
        blog_post.save_revision().publish()

        # Verify all blocks were saved
        assert len(blog_post.body) == 3
        assert blog_post.body[0].block_type == "rich_text"
        assert blog_post.body[1].block_type == "code"
        assert blog_post.body[2].block_type == "rich_text"

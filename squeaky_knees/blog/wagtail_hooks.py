from wagtail import hooks
from wagtail.admin.rich_text.editors.draftail.features import InlineStyleFeature


@hooks.register("register_rich_text_features")
def register_code_style_feature(features):
    """Add inline code styling (Ctrl+`)."""
    feature_name = "code"

    features.register_editor_plugin(
        "draftail",
        feature_name,
        InlineStyleFeature(
            {
                "type": "CODE",
                "icon": "code",
            },
        ),
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {
                "code": {"element": "code"},
            },
            "to_database_format": {
                "style_map": {
                    "CODE": "code",
                },
            },
        },
    )

    if feature_name not in features.default_features:
        features.default_features.append(feature_name)

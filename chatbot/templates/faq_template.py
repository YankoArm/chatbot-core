# chatbot/templates/faq_template.py

FAQ_TEMPLATE = {
    "name": "FAQ Bot",

    "features": {
        "faq": True,
        "human_support": True,
    },

    "menu_items": [
        {
            "id": "faq",
            "feature": "faq",
            "labels": {
                "es": "Ver preguntas frecuentes",
                "en": "View frequently asked questions",
            },
        },
        {
            "id": "human_support",
            "feature": "human_support",
            "labels": {
                "es": "Hablar con una persona",
                "en": "Talk to a person",
            },
        },
    ],

    "menu_footer": {
        "es": "También puedes escribir 'menu' en cualquier momento.",
        "en": "You can also type 'menu' at any time.",
    },

    "menu_title": {
        "es": "Menú principal:",
        "en": "Main menu:",
    },
}
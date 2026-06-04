# chatbot/templates/sales_template.py

SALES_TEMPLATE = {
    "name": "Sales Bot",

    "features": {
        "products": True,
        "promotions": True,
        "human_support": True,
    },

    "menu_items": [
        {
            "id": "products",
            "feature": "products",
            "labels": {
                "es": "Ver productos",
                "en": "View products",
            },
        },
        {
            "id": "promotions",
            "feature": "promotions",
            "labels": {
                "es": "Ver promociones",
                "en": "View promotions",
            },
        },
        {
            "id": "human_support",
            "feature": "human_support",
            "labels": {
                "es": "Hablar con ventas",
                "en": "Talk to sales",
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
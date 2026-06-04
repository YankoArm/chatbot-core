# chatbot/templates/booking_template.py

BOOKING_TEMPLATE = {
    "name": "Booking Bot",

    "features": {
        "sessions": True,
        "prices": True,
        "dates": True,
        "booking": True,
        "human_support": True,
    },

    "menu_items": [
        {
            "id": "sessions",
            "feature": "sessions",
            "labels": {
                "es": "Ver tipos de sesión",
                "en": "View session types",
            },
        },
        {
            "id": "prices",
            "feature": "prices",
            "labels": {
                "es": "Ver precios",
                "en": "View prices",
            },
        },
        {
            "id": "dates",
            "feature": "dates",
            "labels": {
                "es": "Ver fechas disponibles",
                "en": "View available dates",
            },
        },
        {
            "id": "booking",
            "feature": "booking",
            "labels": {
                "es": "Iniciar reserva",
                "en": "Start booking",
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
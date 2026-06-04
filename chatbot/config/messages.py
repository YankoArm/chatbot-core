# chatbot/config/messages.py

MESSAGES = {
    "welcome": {
        "es": (
            "Hola. Gracias por escribir.\n"
            "Voy a ayudarte a gestionar tu consulta de forma rápida."
        ),
        "en": (
            "Hello. Thanks for your message.\n"
            "I will help you manage your consultation quickly."
        ),
    },
    "invalid_option": {
        "es": "Opción no válida. Por favor, elige una de las opciones del menú.",
        "en": "Invalid option. Please choose one of the menu options.",
    },
    "no_booking_to_confirm": {
        "es": (
            "Todavía no has seleccionado una sesión y una fecha.\n"
            "Primero elige la opción 4 para iniciar la reserva."
        ),
        "en": (
            "You have not selected a session and a date yet.\n"
            "Please choose option 4 first to start the booking process."
        ),
    },
    "booking_confirmed": {
        "es": "Reserva confirmada correctamente.",
        "en": "Booking confirmed successfully.",
    },
    "booking_cancelled": {
        "es": "La reserva no se ha confirmado todavía.",
        "en": "The booking has not been confirmed yet.",
    },
    "choose_session_type": {
        "es": "Elige el tipo de sesión:",
        "en": "Choose the session type:",
    },
    "choose_date": {
        "es": "Elige una fecha disponible:",
        "en": "Choose an available date:",
    },
    "back_to_menu": {
        "es": "Escribe 'menu' para volver al menú principal.",
        "en": "Type 'menu' to go back to the main menu.",
    },
    "main_menu": {
        "es": (
            "¿Qué deseas hacer?\n\n"
            "1. Ver tipos de sesiones\n"
            "2. Ver precios\n"
            "3. Ver fechas disponibles\n"
            "4. Reservar sesión\n"
            "5. Hablar con una persona\n\n"
            "Responde con el número de la opción."
        ),
        "en": (
            "What would you like to do?\n\n"
            "1. View session types\n"
            "2. View prices\n"
            "3. Check available dates\n"
            "4. Book a session\n"
            "5. Talk to a person\n\n"
            "Reply with the option number."
        ),
    },
}
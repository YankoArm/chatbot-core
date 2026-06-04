from chatbot.config.knowledge import BUSINESS_INFO


class ContentService:

    @staticmethod
    def get_sessions(language):
        return BUSINESS_INFO["sessions"][language]

    @staticmethod
    def get_prices(language):
        return BUSINESS_INFO["prices"][language]

    @staticmethod
    def get_dates(language):
        return BUSINESS_INFO["available_dates"][language]
    
    @staticmethod
    def get_faq(language):
        return BUSINESS_INFO["faq"][language]
    
    @staticmethod
    def get_products(language):
        return BUSINESS_INFO["products"][language]

    @staticmethod
    def get_promotions(language):
        return BUSINESS_INFO["promotions"][language]
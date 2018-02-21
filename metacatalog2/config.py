"""
Collection of different Configuration objects for the main application.
"""
import os


class Config:
    ELASTIC_NODE = os.environ.get('ELASTIC_NODE', 'http://localhost:9200')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'dev': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
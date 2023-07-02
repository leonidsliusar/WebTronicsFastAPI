DB_LOGIN = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'social_net'
DB_PORT = '5450'
DB_TEST_PORT = '5451'
DB = f'postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@0.0.0.0:{DB_PORT}/{DB_NAME}'
DB_TEST = f'postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@0.0.0.0:{DB_TEST_PORT}/{DB_NAME}'


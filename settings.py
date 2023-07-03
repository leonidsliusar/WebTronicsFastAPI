DB_LOGIN = 'postgres'
DB_PASSWORD = 'postgres'
DB_NAME = 'social_net'
DB_PORT = '5450'
DB_TEST_PORT = '5451'
DB = f'postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@0.0.0.0:{DB_PORT}/{DB_NAME}'
DB_TEST = f'postgresql+asyncpg://{DB_LOGIN}:{DB_PASSWORD}@0.0.0.0:{DB_TEST_PORT}/{DB_NAME}'

token_conf = {
                    'SECRET_KEY': '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7',
                    'ALGORITHM': 'HS256',
                    'ACCESS_TOKEN_EXPIRE_MINUTES': 30
                }
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# --- Base Directory and .env Loading ---
BASE_DIR = Path(__file__).resolve().parent.parent

# Construct the path to the .env file explicitly (assuming it's in the BASE_DIR)
dotenv_path = BASE_DIR / '.env'

# Attempt to load the .env file
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    print(f"SUCCESS: .env file loaded from: {dotenv_path.resolve()}")
else:
    print(f"WARNING: .env file not found at: {dotenv_path.resolve()}. Using environment variables or defaults.")

# --- Debugging: Print loaded environment variables ---
print(f"DEBUG_ENV_DJANGO_SECRET_KEY: {''.join(['*' for _ in range(len(os.getenv('DJANGO_SECRET_KEY',''))-4)])}{os.getenv('DJANGO_SECRET_KEY','')[-4:] if os.getenv('DJANGO_SECRET_KEY','') else 'Not Set in .env'}")
print(f"DEBUG_ENV_DEBUG_MODE: {os.getenv('DEBUG')}")
print(f"DEBUG_ENV_ALLOWED_HOSTS: {os.getenv('DJANGO_ALLOWED_HOSTS')}")


# --- Security Settings ---
SECRET_KEY_FROM_ENV = os.getenv('DJANGO_SECRET_KEY')
DEBUG_STR_FROM_ENV = os.getenv('DEBUG', 'False') # Default to 'False' string if not set
DEBUG = DEBUG_STR_FROM_ENV.lower() in ('true', '1', 't')

if not SECRET_KEY_FROM_ENV:
    if DEBUG:
        print("WARNING: DJANGO_SECRET_KEY not found in .env. Using a default insecure key for DEBUG mode.")
        SECRET_KEY = 'django_insecure_temporary_debug_key_please_set_in_env'
    else:
        # This error should now only trigger if DEBUG is False AND no key is in .env
        raise ValueError("CRITICAL: DJANGO_SECRET_KEY is not set in .env for a non-DEBUG (production-like) environment!")
else:
    SECRET_KEY = SECRET_KEY_FROM_ENV

# ALLOWED_HOSTS
allowed_hosts_env = os.getenv('DJANGO_ALLOWED_HOSTS', '')
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]
elif DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
else:
    # Production requires explicit hosts in .env or environment variables
    ALLOWED_HOSTS = []
    print("WARNING: ALLOWED_HOSTS is empty. This is only okay if DEBUG=True and it defaults to localhost.")
    print("         If this is a production-like environment (DEBUG=False), this will cause errors.")

if not ALLOWED_HOSTS and not DEBUG:
    raise ValueError("CRITICAL: ALLOWED_HOSTS is not set for a non-DEBUG (production-like) environment!")


# --- Application Definition ---
INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'rest_framework',
    'rest_framework_simplejwt',
    'django_oss_storage',
    'main',
    'accounts',
    'ai_generator'
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",# can not
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",# try
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware", # try
]

ROOT_URLCONF = "XRdjangoProject.urls" # 请确保这是你的项目名

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "XRdjangoProject.wsgi.application" # 请确保这是你的项目名

# --- Database Configuration ---
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.getenv('DATABASE_PORT', '3306'),
    }
}
# Check if essential database settings are loaded
if not DATABASES['default']['NAME'] or not DATABASES['default']['USER'] or not DATABASES['default']['PASSWORD']:
    print("WARNING: Database NAME, USER, or PASSWORD not fully loaded from .env. Check .env file.")


# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# --- Internationalization ---
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# --- Static Files ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles" # Uncomment and configure if you use collectstatic

# --- Default Primary Key Field Type ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Custom User Model ---
AUTH_USER_MODEL = 'accounts.CustomUser'

# --- Media Files (User Uploaded Files) ---
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'django_oss_storage.backends.OssMediaStorage'

# --- Alibaba Cloud OSS Configuration ---
OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')
OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')
OSS_DEFAULT_ACL = os.getenv('OSS_DEFAULT_ACL', 'public-read') # Defaulting to public-read as per your .env

# Check if essential OSS settings are loaded
if not OSS_ACCESS_KEY_ID or not OSS_ACCESS_KEY_SECRET or not OSS_ENDPOINT or not OSS_BUCKET_NAME:
    print("WARNING: Alibaba Cloud OSS settings (ID, SECRET, ENDPOINT, BUCKET_NAME) not fully loaded from .env. File uploads will likely fail.")


# --- Django REST Framework Configuration ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

# --- Simple JWT Configuration ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, # Uses the SECRET_KEY defined earlier
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'JTI_CLAIM': 'jti',
}

# --- Celery Configuration ---
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# --- CORS Configuration ---
CORS_ALLOW_ALL_ORIGINS = True # 【临时调试】在开发中，这通常可以接受。
# 对于生产环境，务必设置为False，并配置下面的白名单：
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:5500",  # 你的前端Live Server地址
#     "http://127.0.0.1:5500",
#     # "https://your-production-frontend.com",
# ]

CORS_ALLOW_HEADERS = [ # 确保这些头部被允许
    "accept",
    "accept-encoding",
    "authorization", # 关键，用于JWT
    "content-type",  # 关键，用于POST JSON数据
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# CORS_ALLOW_METHODS = [ # 通常默认值已包含POST，但明确列出无害
#     "DELETE",
#     "GET",
#     "OPTIONS", # 关键，用于预检请求
#     "PATCH",
#     "POST",    # 关键
#     "PUT",
# ]

# XRdjangoProject/settings.py
# ... (其他配置) ...

# Meshy AI Configuration
MESHY_API_KEY = os.getenv('MESHY_API_KEY')
MESHY_TEXT_TO_3D_ENDPOINT = os.getenv('MESHY_TEXT_TO_3D_ENDPOINT')
MESHY_IMAGE_TO_3D_ENDPOINT = os.getenv('MESHY_IMAGE_TO_3D_ENDPOINT')
MESHY_MULTI_IMAGE_TO_3D_ENDPOINT = os.getenv('MESHY_MULTI_IMAGE_TO_3D_ENDPOINT')
MESHY_TEXT_TO_TEXTURE_ENDPOINT = os.getenv('MESHY_TEXT_TO_TEXTURE_ENDPOINT')

# 检查Meshy API Key是否加载
if not MESHY_API_KEY:
    print("WARNING: MESHY_API_KEY not found in .env. AI generation features will likely fail.")

print("--- SETTINGS.PY LOADED ---")
print(f"DEBUG mode is: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"SECRET_KEY is set (showing last 4 chars for verification): {''.join(['*' for _ in range(len(SECRET_KEY)-4)])}{SECRET_KEY[-4:] if SECRET_KEY else 'None'}")
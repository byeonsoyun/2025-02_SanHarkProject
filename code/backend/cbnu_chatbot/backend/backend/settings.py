from pathlib import Path
import os
from dotenv import load_dotenv # 새로 추가

# .env 파일 로드
load_dotenv() # 프로젝트 루트의 .env 파일을 읽어 os.environ에 반영합니다.
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# DB연동2차추가_API 키 설정을 위해 환경 변수에서 로드 (실제 키는 .env 파일에 저장)
LAW_API_KEY = os.environ.get('LAW_API_KEY') # 더미 키 제거, 실제 키 로드
LAW_API_URL = "http://www.law.go.kr/DRC/lawService.do"
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-s16-*chw3a)#u$7$t^vl_)h58j7@icu4sby$g(h__w$(j#snf5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"] # 개발 편의를 위해 "*"로 변경


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "corsheaders",
    "channels",
    "api",
    "chat", 
    "user_mgmt", 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = "backend.asgi.application" 


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cbnu_chatbot_db'),
        'USER': os.environ.get('DB_USER', 'cbnu_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '1111'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'ko-kr' # 한국어 환경으로 변경
TIME_ZONE = 'Asia/Seoul' # 시간대 한국으로 변경

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 개발 편의 (나중엔 정확한 Origins만 허용하세요)
CORS_ALLOW_ALL_ORIGINS = True


# ASGI 및 Channels 설정
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer", # 개발용. 프로덕션은 Redis 권장
    }
}


# 미디어파일 저장&접근
MEDIA_URL = "/media/" 
MEDIA_ROOT = os.path.join(BASE_DIR, "media") 


# ===============================================
# LLM (Large Language Model) 설정 - Ollama 사용 (services.py에서 참조)
# ===============================================

# 환경 변수에서 가져오거나 기본값 사용
LLM_API_URL = os.environ.get("LLM_API_URL", "http://localhost:22434/api/generate")
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "cbnu1")
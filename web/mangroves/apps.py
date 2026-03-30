from django.apps import AppConfig

class MangrovesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mangroves"

    # Tidak perlu signal di sini karena pemicu tiles sudah di dalam models.save()
    # Kalau nanti mau pakai Celery/queue, barulah pindah trigger ke signal.

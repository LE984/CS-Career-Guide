from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AiIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_integration'
    
    def ready(self):
        # Wait until tables exist; ready() also runs before the first migrate.
        post_migrate.connect(
            self.initialize_prompts_after_migrate,
            sender=self,
            dispatch_uid="ai_integration.initialize_prompts",
        )

    def initialize_prompts_after_migrate(self, sender, using, **kwargs):
        if using == "default":
            from ai_integration.langgraph.utils.prompt_manager import initialize_prompts
            initialize_prompts()

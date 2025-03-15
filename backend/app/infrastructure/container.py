from dependency_injector import containers, providers
from app.application.use_cases.submit_request_use_case import SubmitRequestUseCase
from app.application.use_cases.process_response_use_case import ProcessResponseUseCase
from app.application.use_cases.manage_session_lifecycle_use_case import ManageSessionLifecycleUseCase
from app.infrastructure.adapters.persistence.repository_impl import ConversationRepository
from app.infrastructure.adapters.gpt.gpt_api_adapter import GPTAPIAdapter
from app.infrastructure.event_bus import EventBus
from app.domain.conversation_repository import ConversationRepository  # New import

class Container(containers.DeclarativeContainer):
    """IoC container for dependency injection."""

    config = providers.Configuration()

    # Core services
    event_bus = providers.Singleton(EventBus)
    event_publisher = providers.Factory(lambda event_bus: event_bus.publish, event_bus=event_bus)

    # Adapters
    gpt_service = providers.Singleton(GPTAPIAdapter)
    conversation_repository = providers.Singleton(ConversationRepository)

    # Use cases
    submit_request_use_case = providers.Singleton(
        SubmitRequestUseCase,
        gpt_service=gpt_service,
        conversation_repository=conversation_repository
    )

    # Infrastructure adapters
    persistence = providers.Singleton(
        ConversationRepository,
        event_bus=event_bus
    )

    gpt_api = providers.Singleton(
        GPTAPIAdapter,
        api_key=config.gpt_api_key,
        event_bus=event_bus
    )

    # Use cases with their dependencies
    submit_use_case = providers.Factory(
        SubmitRequestUseCase,
        gpt_api=gpt_api,
        persistence=persistence,
        event_publisher=event_publisher
    )

    process_use_case = providers.Factory(
        ProcessResponseUseCase,
        persistence=persistence,
        event_publisher=event_publisher
    )

    session_use_case = providers.Factory(
        ManageSessionLifecycleUseCase,
        session_repository=persistence
    )

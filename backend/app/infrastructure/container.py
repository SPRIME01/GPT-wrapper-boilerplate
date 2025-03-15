from dependency_injector import containers, providers
from app.application.use_cases.submit_request_use_case import SubmitRequestUseCase
from app.application.use_cases.process_response_use_case import ProcessResponseUseCase
from app.application.use_cases.manage_session_lifecycle_use_case import ManageSessionLifecycleUseCase
from app.application.services.cache_service import CacheService
from app.application.services.rate_limiter_service import RateLimiterService
from app.infrastructure.adapters.persistence.repository_impl import ConversationRepository
from app.infrastructure.adapters.gpt.gpt_api_adapter import GPTAPIAdapter
from app.infrastructure.adapters.cache.cache_adapter import InMemoryCacheAdapter, RedisCacheAdapter
from app.infrastructure.adapters.rate_limiting.rate_limiter import InMemoryRateLimiter, RedisRateLimiter
from app.infrastructure.event_bus import EventBus
from app.domain.conversation_repository import ConversationRepository  # New import

class Container(containers.DeclarativeContainer):
    """IoC container for dependency injection."""

    config = providers.Configuration()

    # Core services
    event_bus = providers.Singleton(EventBus)
    event_publisher = providers.Factory(lambda event_bus: event_bus.publish, event_bus=event_bus)

    # Cache components
    cache_adapter = providers.Factory(
        lambda cache_type=None, redis_url=None:
            RedisCacheAdapter(redis_url) if cache_type == 'redis' and redis_url
            else InMemoryCacheAdapter(),
        cache_type=config.cache_type.as_(str, None),
        redis_url=config.redis_url.as_(str, None)
    )

    cache_service = providers.Singleton(
        CacheService,
        cache_adapter=cache_adapter
    )

    # Rate limiting components
    rate_limiter = providers.Factory(
        lambda rate_limiter_type=None, redis_url=None:
            RedisRateLimiter(redis_url) if rate_limiter_type == 'redis' and redis_url
            else InMemoryRateLimiter(),
        rate_limiter_type=config.rate_limiter_type.as_(str, None),
        redis_url=config.redis_url.as_(str, None)
    )

    rate_limiter_service = providers.Singleton(
        RateLimiterService,
        rate_limiter=rate_limiter
    )

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
        api_key=config.gpt_api_key.as_(str, None),
        event_bus=event_bus,
        cache_service=cache_service,  # Inject cache service
        rate_limiter_service=rate_limiter_service  # Inject rate limiter service
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
        event_publisher=event_publisher,
        cache_service=cache_service
    )

    session_use_case = providers.Factory(
        ManageSessionLifecycleUseCase,
        session_repository=persistence
    )

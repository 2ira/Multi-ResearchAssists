from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from config_loader import config_loader
from autogen_core.models import ModelInfo

"""
For some client examples:

openai_model_client = OpenAIChatCompletionClient(
    model="gpt-4o-2024-08-06",
    # api_key="sk-...", # Optional if you have an OPENAI_API_KEY environment variable set.
)

model_client = OpenAIChatCompletionClient(
model="gemini-2.0-flash-lite",
model_info=ModelInfo(vision=True, function_calling=True, json_output=True, family="unknown", structured_output=True)
# api_key="GEMINI_API_KEY",
)

sk_client = AnthropicChatCompletion(
    ai_model_id="claude-3-5-sonnet-20241022",
    api_key=os.environ["ANTHROPIC_API_KEY"],
    service_id="my-service-id",  # Optional; for targeting specific services within Semantic Kernel
)
settings = AnthropicChatPromptExecutionSettings(
    temperature=0.2,
)

anthropic_model_client = SKChatCompletionAdapter(
    sk_client, kernel=Kernel(memory=NullMemory()), prompt_settings=settings
)
"""


def create_model_client(
        model_config_name: str = "default_model") -> OpenAIChatCompletionClient | AnthropicChatCompletionClient:
    """
    support OpenAI、Gemini,Claude all succeed ChatCompletionClient
    usage:
        # 创建客户端
        openai_client = create_model_client("default_model")
        gemini_client = create_model_client("gemini_model")
        claude_client = create_model_client("claude_model")
        # 统一接口调用
        async def get_response(client, messages):
            return await client.create(messages)

    """
    model_config = config_loader.get_model_config(model_config_name)
    print(f"Use model config is ",model_config)
    model_type = model_config.get("type", "").lower()
    print(f" Use model type is {model_type}")
    common_params = {
        "model": model_config.get("name"),
        "api_key": model_config.get("api_key"),
        "base_url": model_config.get("base_url"),
    }
    # get model parameters
    params = model_config.get("parameters", {})

    if model_type in ["openai", "gemini"]:
        if model_type == "gemini":
            # make sure Gemini information is correct
            params.setdefault("model_info", ModelInfo(
                vision=params.get("vision", False),
                function_calling=params.get("function_calling", False),
                json_output=params.get("json_output", False),
                family=params.get("family", "unknown"),
                structured_output=params.get("structured_output", True)
            ))
        return OpenAIChatCompletionClient(**common_params, **params)

    elif model_type == "claude":
        return AnthropicChatCompletionClient(**common_params, **params)

    else:
        raise ValueError(f"Unsupported model type: {model_type}. Supported types: openai, gemini, claude")

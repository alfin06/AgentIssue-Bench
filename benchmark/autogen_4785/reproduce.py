from autogen_ext.models import OpenAIChatCompletionClient

groq_model_client = OpenAIChatCompletionClient(
model='llama3-groq-70b-8192-tool-use-preview',
base_url="https://openkey.cloud/v1",
api_key=""
)
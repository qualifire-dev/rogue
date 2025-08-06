# LLM Provider Configuration

The TUI now includes a comprehensive LLM provider configuration dialog that allows users to configure API keys for different LLM providers and access their available models.

## Features

- **Multi-Provider Support**: Configure OpenAI, Anthropic, Google AI, and Cohere
- **Secure API Key Input**: Masked input for security
- **Model Selection**: Browse and select available models for each provider
- **Configuration Status**: Visual indicators for configured providers
- **Step-by-Step Wizard**: Guided configuration process
- **Integration**: Seamlessly integrates with existing config system

## Supported Providers

### OpenAI
- **Models**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **API Key**: OPENAI_API_KEY
- **Features**: Chat completions, embeddings

### Anthropic
- **Models**: Claude-3 Opus, Claude-3 Sonnet, Claude-3 Haiku
- **API Key**: ANTHROPIC_API_KEY
- **Features**: Chat completions, long context

### Google AI
- **Models**: Gemini Pro, Gemini Pro Vision
- **API Key**: GOOGLE_API_KEY
- **Features**: Multimodal capabilities

### Cohere
- **Models**: Command, Command Light, Command Nightly
- **API Key**: COHERE_API_KEY
- **Features**: Text generation, embeddings

## Usage

### Opening the Configuration Dialog

#### Via Command
Type `/models` in the command input to open the LLM configuration dialog.

#### Via Keyboard Shortcut
Press **Ctrl+M** to quickly open the configuration dialog.

### Configuration Steps

#### Step 1: Provider Selection
- Use **Up/Down arrows** to navigate between providers
- Providers with existing configuration show a **✓** indicator and display available models
- Configured providers skip directly to model selection for quick access
- Unconfigured providers proceed to API key input
- Clean, sleek design with primary color highlighting for selected provider
- Press **Enter** or click **Next** to proceed

#### Step 2: API Key Input
- Enter your API key for the selected provider
- Input is masked with asterisks for security
- Use **Ctrl+A** to go to beginning, **Ctrl+E** to go to end
- The environment variable name is displayed for reference
- Press **Enter** or click **Validate** to proceed

#### Step 3: Model Selection
- Browse available models for the provider
- Use **Up/Down arrows** to navigate models
- Models are fetched based on your API key access
- Press **Enter** or click **Configure** to complete setup

#### Step 4: Completion
- Configuration is saved to the application config
- Success message displays configured provider and model
- API key is stored securely in the config system

### Navigation Controls

- **Up/Down Arrows**: Navigate lists (providers, models)
- **Tab/Shift+Tab**: Navigate buttons
- **Enter**: Confirm selection or proceed to next step
- **Escape**: Cancel configuration and close dialog
- **Ctrl+A/Ctrl+E**: Navigate to start/end of API key input

## Configuration Storage

API keys are stored in the application's configuration system:

```toml
[api_keys]
openai = "sk-..."
anthropic = "sk-ant-..."
google = "AIza..."
cohere = "..."
```

## Security Features

- **Masked Input**: API keys are displayed as asterisks during input
- **Secure Storage**: Keys are stored in the application config
- **No Logging**: API keys are not logged or displayed in plain text
- **Validation**: Keys are validated before saving

## Error Handling

- **Empty API Key**: Warning displayed if API key is empty
- **Invalid API Key**: Validation errors are shown with helpful messages
- **Network Issues**: Graceful handling of API connectivity problems
- **Provider Errors**: Clear error messages for provider-specific issues

## Integration with Evaluation System

Once configured, LLM providers can be used for:
- **Agent Evaluations**: Run evaluations against configured models
- **Model Comparisons**: Compare performance across different providers
- **Scenario Testing**: Test scenarios with various LLM backends
- **Batch Processing**: Process multiple evaluations with different models

## Example Workflow

1. **Open Configuration**: Type `/models` or press **Ctrl+M**
2. **Select Provider**: Choose "OpenAI" from the list
3. **Enter API Key**: Input your OpenAI API key
4. **Choose Model**: Select "gpt-4" from available models
5. **Complete Setup**: Configuration is saved and ready to use
6. **Start Evaluation**: Use the configured model for agent evaluations

## Tips

- **Multiple Providers**: Configure multiple providers for comparison
- **Model Selection**: Different models have different capabilities and costs
- **API Key Management**: Keep your API keys secure and rotate them regularly
- **Testing**: Test your configuration with a simple evaluation first
- **Updates**: Reconfigure providers when you get new API keys or access to new models

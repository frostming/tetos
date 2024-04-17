# unitts

A unified interface for multiple Text-to-Speech (TTS) providers.


## Supported TTS providers

- [Edge-TTS](https://github.com/rany2/edge-tts)
- [OpenAI TTS](https://platform.openai.com/docs/guides/text-to-speech)

  Required parameters:

  - `api_key`: OpenAI API key

- [Azure TTS](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/text-to-speech)

  Required parameters(Please refer to the documentation to get the secrets):

  - `speech_key`: Azure Speech service key
  - `service_region`: Azure Speech service region


## Installation

Requires Python 3.8 or higher.

```bash
pip install unitts
```

## CLI Usage

```
unitts PROVIDER [PROVIDER_OPTIONS] TEXT [--output FILE]
```

Please run `unitts --help` for available providers and options.

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

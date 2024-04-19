# TeToS
<!--index start-->

[![PyPI](https://img.shields.io/pypi/v/tetos)](https://pypi.org/project/tetos/)
[![Python](https://img.shields.io/pypi/pyversions/tetos)](https://pypi.org/project/tetos/)
[![License](https://img.shields.io/pypi/l/tetos)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://pepy.tech/badge/tetos)](https://pepy.tech/project/tetos)
[![Documentation Status](https://readthedocs.org/projects/tetos/badge/?version=latest)](https://tetos.readthedocs.io/latest/?badge=latest)

A unified interface for multiple Text-to-Speech (TTS) providers.


## Supported TTS providers

- [Edge-TTS](https://github.com/rany2/edge-tts)
- [OpenAI TTS](https://platform.openai.com/docs/guides/text-to-speech)

  Required parameters:

  - `api_key`: OpenAI API key

- [Azure TTS](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/text-to-speech)

  Required parameters(Please refer to the documentation to get the secrets):

  - `speech_key`: Azure Speech service key
  - `speech_region`: Azure Speech service region

- [Google TTS](https://cloud.google.com/text-to-speech?hl=zh-CN)

  Requirements:

  - [Enable the Text-to-Speech API in the Google Cloud Console](https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=586547753837)
  - Environment variables `GOOGLE_APPLICATION_CREDENTIALS` pointing to the service account key file

- [Volcengine TTS(火山引擎)](https://console.volcengine.com/sami)

  Required parameters:

  - `access_key`: Volcengine access key ID. ([Get it here](https://console.volcengine.com/iam/keymanage/))
  - `secret_key`: Volcengine access secret key. ([Get it here](https://console.volcengine.com/iam/keymanage/))
  - `app_key`: Volcengine app key

- [Baidu TTS](https://ai.baidu.com/tech/speech/tts)

  Required parameters:

  - `api_key`: Baidu API key
  - `secret_key`: Baidu secret key

  [Get both at the console](https://console.bce.baidu.com/ai/#/ai/speech/app/list)


## Installation

Requires Python 3.8 or higher.

```bash
pip install tetos
```

## CLI Usage

```
tetos PROVIDER [PROVIDER_OPTIONS] TEXT [--output FILE]
```

Please run `tetos --help` for available providers and options.

Examples

```
tetos google "Hello, world!"
tetos azure "Hello, world!" --output output.mp3   # save to another file
tetos edge --lang zh-CN "你好，世界！"  # specify language
tetos openai --voice echo "Hello, world!"  # specify voice
```

## API Usage

Use Azure TTS as an example:

```python
from tetos.azure import AzureSpeaker

speaker = AzureSpeaker(speech_key='...', speech_region='...')
speaker.say('Hello, world!', 'output.mp3')
```

The initialization parameters may be different for other providers.

## Behind a proxy

TeTos respects the proxy environment variables `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY`.

## TODO

- [x] Google TTS
- [ ] SSML support

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

<!--index end-->

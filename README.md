# TeToS
<!--index start-->

[![PyPI](https://img.shields.io/pypi/v/tetos)](https://pypi.org/project/tetos/)
[![Python](https://img.shields.io/pypi/pyversions/tetos)](https://pypi.org/project/tetos/)
[![License](https://img.shields.io/pypi/l/tetos)](https://www.apache.org/licenses/LICENSE-2.0)
[![Downloads](https://pepy.tech/badge/tetos)](https://pepy.tech/project/tetos)
[![Documentation Status](https://readthedocs.org/projects/tetos/badge/?version=latest)](https://tetos.readthedocs.io/latest/?badge=latest)

A unified interface for multiple Text-to-Speech (TTS) providers.


## Supported TTS providers

| Provider                                                                                             | Requirements                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Edge-TTS](https://github.com/rany2/edge-tts)                                                        | -                                                                                                                                                                                                                                                                 |
| [OpenAI TTS](https://platform.openai.com/docs/guides/text-to-speech)                                 | `api_key`: OpenAI API key                                                                                                                                                                                                                                         |
| [Azure TTS](https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/text-to-speech) | `speech_key`: Azure Speech service key<br>`speech_region`: Azure Speech service region                                                                                                                                                                            |
| [Google TTS](https://cloud.google.com/text-to-speech?hl=zh-CN)                                       | [Enable the Text-to-Speech API in the Google Cloud Console](https://console.developers.google.com/apis/api/texttospeech.googleapis.com/overview?project=586547753837)<br>Set env var `GOOGLE_APPLICATION_CREDENTIALS` as the path to the service account key file |
| [Volcengine TTS(火山引擎)](https://console.volcengine.com/sami)                                      | `access_key`: Volcengine access key ID. ([Get it here](https://console.volcengine.com/iam/keymanage/))<br>`secret_key`: Volcengine access secret key. ([Get it here](https://console.volcengine.com/iam/keymanage/))<br>`app_key`: Volcengine app key             |
| [Baidu TTS](https://ai.baidu.com/tech/speech/tts)                                                    | `api_key`: Baidu API key<br>`secret_key`: Baidu secret key<br>Both can be acquired at the [console](https://console.bce.baidu.com/ai/#/ai/speech/app/list)                                                                                                        |
| [Minimax TTS](https://www.minimaxi.com/document/speech-synthesis-engine?id=645e034eeb82db92fba9ac20) | `api_key`: Minimax API key<br>`group_id`: Minimax group ID<br>Both can be acquired at the [Minimax console](https://www.minimaxi.com/user-center/basic-information)                                                                                               |
| [迅飞 TTS](https://www.xfyun.cn/services/online_tts)                                                 | `app_id`: Xunfei APP ID<br>`api_key`: Xunfei API key<br>`api_secret`: Xunfei API secret                                                                                                                                                                           |
| [Fish Audio](https://fish.audio)                                                                     | `api_key`: Fish Audio API key                                                                                                                                                                                                                                     |

## Installation

Tetos requires Python 3.8 or higher.

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

## Work behind a proxy

TeTos respects the proxy environment variables `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY`.

## TODO

- [x] Google TTS
- [ ] SSML support

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

<!--index end-->

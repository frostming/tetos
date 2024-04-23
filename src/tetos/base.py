from __future__ import annotations

import abc
from pathlib import Path
from typing import Any, Callable, TypeVar

import click

F = TypeVar("F", bound=Callable[..., Any])


class SynthesizeError(RuntimeError):
    pass


class Speaker(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def synthesize(
        self, text: str, out_file: str | Path, lang: str = "en-US"
    ) -> float:
        """Generate speech from text and save it to a file.

        Args:
            text (str): The text to synthesize.
            out_file (Path): The file to save the speech to.
            lang (str): The language code of the text. e.g. "en-US", "fr-FR".

        Returns:
            float: The duration of the speech in seconds.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def list_voices(cls) -> list[str]:
        """List the available voices for the speaker.

        Returns:
            list[str]: A list of voice names.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def get_command(cls) -> click.Command:
        """Return a Click command for the speaker.

        Returns:
            click.Command: The Click command.
        """
        raise NotImplementedError

    def say(
        self, text: str, out_file: str | Path | None = None, lang: str = "en-US"
    ) -> float:
        """A synchronous version of synthesize()

        Args:
            text (str): The text to synthesize.
            out_file (Path): The file to save the speech to.
            lang (str): The language code of the text. e.g. "en-US", "fr-FR".
        """
        import anyio
        import click

        if out_file is None:
            out_file = Path("tts-output.mp3")

        result = anyio.run(self.synthesize, text, out_file, lang)
        click.echo(f"Speech is generated successfully at {out_file}")
        return result


def common_options(cls: Speaker) -> Callable[[F], F]:
    def list_voices(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        click.echo("\n".join(cls.list_voices()))
        ctx.exit()

    def decorator(func: F) -> F:
        func = click.argument("text")(func)
        func = click.option(
            "--output",
            "-o",
            type=click.Path(dir_okay=False),
            default="tts-output.mp3",
            help="The output file.",
        )(func)
        func = click.option(
            "--voice",
            help="The voice to use. See supported voices with `--list-voices`",
        )(func)
        func = click.option(
            "--lang",
            default="en-US",
            help="The language code of the text. e.g. 'en-US', 'fr-FR'.",
        )(func)
        func = click.option(
            "--list-voices",
            "-l",
            is_flag=True,
            help="List available voices.",
            is_eager=True,
            callback=list_voices,
            expose_value=False,
        )(func)
        return func

    return decorator


def filter_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}

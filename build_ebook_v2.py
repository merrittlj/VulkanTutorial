# """Generates epub and pdf from sources."""

import pathlib
import re
import subprocess


class VTLogger:
    """A logger"""
    def __init__(self, filename:str, log_to_file:bool=True):
        if log_to_file is True:
            self.log_file = open(filename, "w", encoding="utf-8")

    def __del__(self):
        if self.log_file is not None:
            self.log_file.close()

    def detail(self, message: str):
        """Logs a detail message without printing it."""
        self._log(message, True)

    def error(self, message: str):
        """Logs an error."""
        message = f"Error: {message}"
        self._log(message)

    def info(self, message: str):
        """Logs an info message."""
        print(message)
        self._log(f"Info: {message}", True)

    def warning(self, message: str):
        """Logs an warning."""
        message = f"Warning: {message}"
        self._log(message)

    def _log(self, message: str, no_print:bool=False):
        if no_print is False:
            print(message)

        if self.log_file is not None:
            self.log_file.write(f"{message}\n")

class VTEMarkdownFile:
    """Markdown file."""

    def __init__(self, content: str, depth: int, prefix: str, title: str) -> None:
        self.content: str = content
        self.depth: str = depth
        self.prefix: str = prefix
        self.title: str = title

    def __repr__(self):
        return (
            f"<VTEMarkdownFile depth: {self.depth}, prefix: '{self.prefix}',"
            f" title: '{self.title}', content: '{self.content}'>"
        )

    def __str__(self):
        return (
            f"<VTEMarkdownFile depth: {self.depth}, prefix: '{self.prefix}',"
            f" title: '{self.title}', content: '{self.content}'>"
        )

class VTEBookBuilder:
    """A 'Markdown' to 'epub' and 'pdf' converter."""

    def __init__(self, logger: VTLogger):
        self.log = logger

    def build_pdf_book(self, language: str):
        """Builds a pdf file"""

        self.log.info("Building 'pdf'...")

        subprocess.check_output(
            [
                'pandoc',
                'ebook.md',
                '-V', 'documentclass=report',
                '-t', 'latex',
                '-s',
                '--toc',
                '--listings',
                '-H', 'ebook/listings-setup.tex',
                '-o', 'ebook/Vulkan Tutorial ' + language + '.pdf',
                '--pdf-engine=xelatex'
            ]
        )

    def build_epub_book(self, language: str):
        """Buids a epub file"""

        self.log.info("Building 'epub'...")

        subprocess.check_output(
            [
                'pandoc',
                'ebook.md',
                '--toc',
                '-o', 'ebook/Vulkan Tutorial ' + language + '.epub',
                '--epub-cover-image=ebook/cover.png'
            ]
        )

    def convert_svg_to_png(self, images_folder: str) -> list[pathlib.Path]:
        """Converts *.svg images to *.png using Inkscape"""

        self.log.info("Converting 'svg' images...")

        pngs = list[pathlib.Path]()

        for entry in pathlib.Path(images_folder).iterdir():
            if entry.suffix == ".svg":
                new_path = entry.with_suffix(".png")
                try:
                    # subprocess.check_output(
                    #     [
                    #         'inkscape',
                    #         '--export-filename=' + new_path.as_posix(),
                    #         new_path.parent.as_posix() + "/" + new_path.stem
                    #     ],
                    #     stderr=subprocess.STDOUT
                    # )
                    pngs.append(new_path)
                except FileNotFoundError as error:
                    self.log.error(error)
                    self.log.warning("Install 'Inkscape' (https://www.inkscape.org)!")

                    raise RuntimeError from error

        return pngs

    def generate_markdown_from_sources(self, language: str, output_filename: pathlib.Path):
        """Processes the markdown sources and produces a joined file."""

        self.log.info(
            f"Generating a temporary 'Markdown' file: '{output_filename}'" \
            f" for language '{language}'..."
        )

        md_files = self._process_files_in_directory(language)
        md_files = sorted(md_files, key=lambda file: file.prefix)

        temp_markdown: str = str()

        for entry in md_files:
            # Add title.
            content: str = '# ' + entry.title + '\n\n' + entry.content

            # Fix image links.
            content = re.sub(r'\/images\/', 'images/', content)
            content = re.sub(r'\.svg', '.png', content)

            # Fix remaining relative links (e.g. code files).
            content = re.sub(r'\]\(\/', '](https://vulkan-tutorial.com/', content)

            # Fix chapter references
            def repl(match):
                target = match.group(1)
                target = target.lower()
                target = re.sub('_', '-', target)
                target = target.split('/')[-1]

                return '](#' + target + ')'

            content = re.sub(r'\]\(!([^)]+)\)', repl, content)

            temp_markdown += content + '\n\n'

        log.info("Writing markdown file...")

        with open(output_filename, "w", encoding="utf-8") as file:
            file.write(temp_markdown)

    def _process_files_in_directory(
        self,
        directory_path: pathlib.Path,
        current_depth: int=int(0),
        parent_prefix: str=str(),
        markdown_files: list[VTEMarkdownFile]=None
    ) -> list[VTEMarkdownFile]:
        """Traverses the directory tree, processes `Markdown` files."""
        if markdown_files is None:
            markdown_files = list[VTEMarkdownFile]()

        for entry in pathlib.Path(directory_path).iterdir():
            title_tokens = entry.stem.replace('_', ' ').split(" ")
            prefix = f"{parent_prefix}{title_tokens[0]}."

            if entry.is_dir() is True:
                log.info(f"Processing directory: {entry}")

                self._process_files_in_directory(entry, (current_depth + 1), prefix, markdown_files)
            else:
                log.info(f"Processing: {entry}")

                title = ' '.join(title_tokens[1:])

                with open(entry, 'r', encoding="utf-8") as file:
                    content = file.read()
                    markdown_files.append(VTEMarkdownFile(content, current_depth, prefix, title))

        return markdown_files


###############################################################################


if __name__ == "__main__":

    log = VTLogger("./build_ebook.log")
    eBookBuilder = VTEBookBuilder(log)

    generated_pngs = eBookBuilder.convert_svg_to_png("./images")

    LANGUAGES = [ "en", "fr" ]
    OUTPUT_FILENAME = pathlib.Path("./temp_ebook.md")

    for lang in LANGUAGES:
        lang = f"./{lang}"

        eBookBuilder.generate_markdown_from_sources(lang, OUTPUT_FILENAME)

        # eBookBuilder.build_epub_book(lang)
        # eBookBuilder.build_pdf_book(lang)

        # Clean up
        OUTPUT_FILENAME.unlink()

    # Clean up temporary files
    for png_path in generated_pngs:
        try:
            png_path.unlink()
        except FileNotFoundError as fileError:
            log.error(fileError)

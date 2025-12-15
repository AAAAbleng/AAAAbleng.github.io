#!/usr/bin/env python3
"""
EPUB to Markdown Converter with Tkinter GUI
Converts EPUB files to Markdown format with metadata and assets
"""

import html2text
import os
import json
import re
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from html import unescape
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from typing import List, Dict, Tuple, Optional


def check_and_install_dependencies():
    """检查并自动安装所需的依赖"""
    required_packages = {
        'html2text': 'html2text'
    }

    missing_packages = []

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print(f"检测到缺失的依赖包: {', '.join(missing_packages)}")
        print("正在自动安装...")

        for package in missing_packages:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package])
                print(f"✓ 成功安装 {package}")
            except subprocess.CalledProcessError:
                print(f"✗ 安装 {package} 失败，请手动安装: pip install {package}")
                return False

        print("所有依赖已安装完成！\n")

    return True


# 检查依赖
if not check_and_install_dependencies():
    input("按回车键退出...")
    sys.exit(1)

# 现在安全地导入 html2text


class EpubConverter:
    """Core EPUB conversion logic"""

    def __init__(self, output_base_dir: str = "books_src"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)

    def slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')

    def extract_epub_metadata(self, epub_path: str) -> Dict:
        """Extract metadata from EPUB file"""
        metadata = {
            'title': 'Unknown Title',
            'author': 'Unknown Author',
            'description': ''
        }

        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # Find OPF file
                container_path = 'META-INF/container.xml'
                if container_path in epub.namelist():
                    container_content = epub.read(container_path)
                    container_root = ET.fromstring(container_content)
                    ns = {
                        'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                    rootfile = container_root.find('.//container:rootfile', ns)

                    if rootfile is not None:
                        opf_path = rootfile.get('full-path')
                        opf_content = epub.read(opf_path)
                        opf_root = ET.fromstring(opf_content)

                        # Extract metadata
                        ns_dc = {'dc': 'http://purl.org/dc/elements/1.1/'}

                        title_elem = opf_root.find('.//dc:title', ns_dc)
                        if title_elem is not None and title_elem.text:
                            metadata['title'] = title_elem.text.strip()

                        creator_elem = opf_root.find('.//dc:creator', ns_dc)
                        if creator_elem is not None and creator_elem.text:
                            metadata['author'] = creator_elem.text.strip()

                        desc_elem = opf_root.find('.//dc:description', ns_dc)
                        if desc_elem is not None and desc_elem.text:
                            metadata['description'] = desc_elem.text.strip()

        except Exception as e:
            print(f"Error extracting metadata: {e}")

        return metadata

    def extract_toc_from_epub(self, epub_path: str) -> List[Dict]:
        """Extract table of contents from EPUB"""
        chapters = []

        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # Find OPF file
                container_path = 'META-INF/container.xml'
                container_content = epub.read(container_path)
                container_root = ET.fromstring(container_content)
                ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
                rootfile = container_root.find('.//container:rootfile', ns)

                if rootfile is not None:
                    opf_path = rootfile.get('full-path')
                    opf_dir = str(Path(opf_path).parent)
                    opf_content = epub.read(opf_path)
                    opf_root = ET.fromstring(opf_content)

                    # Get spine items (reading order)
                    ns_opf = {'opf': 'http://www.idpf.org/2007/opf'}
                    spine = opf_root.find('.//opf:spine', ns_opf)
                    manifest = opf_root.find('.//opf:manifest', ns_opf)

                    if spine is not None and manifest is not None:
                        for idx, itemref in enumerate(spine.findall('.//opf:itemref', ns_opf), 1):
                            idref = itemref.get('idref')
                            item = manifest.find(
                                f".//opf:item[@id='{idref}']", ns_opf)

                            if item is not None:
                                href = item.get('href')
                                if href:
                                    # Construct full path
                                    if opf_dir and opf_dir != '.':
                                        full_path = f"{opf_dir}/{href}"
                                    else:
                                        full_path = href

                                    # Read content to get title
                                    try:
                                        content = epub.read(full_path).decode(
                                            'utf-8', errors='ignore')
                                        title = self.extract_title_from_html(
                                            content)

                                        if not title:
                                            title = f"Chapter {idx}"

                                        chapters.append({
                                            'order': idx,
                                            'title': title,
                                            'content': content,
                                            'original_path': full_path
                                        })
                                    except:
                                        continue

        except Exception as e:
            print(f"Error extracting TOC: {e}")

        return chapters

    def extract_title_from_html(self, html_content: str) -> str:
        """Extract title from HTML content"""
        try:
            # Try to find h1-h6 tags
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                match = re.search(
                    f'<{tag}[^>]*>(.+?)</{tag}>', html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    title = re.sub('<[^<]+?>', '', match.group(1))
                    title = unescape(title).strip()
                    if title:
                        return title

            # Try title tag
            match = re.search(r'<title>(.+?)</title>',
                              html_content, re.IGNORECASE)
            if match:
                return unescape(match.group(1)).strip()

        except:
            pass

        return ""

    def html_to_markdown(self, html_content: str, assets_dir: Path, chapter_slug: str) -> str:
        """Convert HTML to Markdown"""
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = False
        h2t.ignore_emphasis = False
        h2t.body_width = 0

        markdown = h2t.handle(html_content)

        # Fix image paths to point to assets directory
        markdown = re.sub(
            r'!\[(.*?)\]\((.*?)\)',
            lambda m: f'![{m.group(1)}](assets/{Path(m.group(2)).name})',
            markdown
        )

        return markdown

    def extract_assets(self, epub_path: str, output_dir: Path) -> None:
        """Extract images and other assets from EPUB"""
        assets_dir = output_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)

        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                for name in epub.namelist():
                    # Extract image files
                    if any(name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']):
                        try:
                            content = epub.read(name)
                            filename = Path(name).name
                            output_path = assets_dir / filename

                            with open(output_path, 'wb') as f:
                                f.write(content)
                        except:
                            continue

        except Exception as e:
            print(f"Error extracting assets: {e}")

    def convert_epub(self, epub_path: str, log_callback=None) -> Optional[Dict]:
        """Convert a single EPUB file"""
        try:
            if log_callback:
                log_callback(f"Processing: {Path(epub_path).name}\n")

            # Extract metadata
            metadata = self.extract_epub_metadata(epub_path)
            book_slug = self.slugify(metadata['title'])
            book_id = book_slug

            if log_callback:
                log_callback(f"  Book: {metadata['title']} (ID: {book_id})\n")

            # Create output directory
            output_dir = self.output_base_dir / book_id
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True)

            # Extract chapters
            chapters = self.extract_toc_from_epub(epub_path)

            if not chapters:
                if log_callback:
                    log_callback(f"  Warning: No chapters found\n")
                return None

            if log_callback:
                log_callback(f"  Found {len(chapters)} chapters\n")

            # Extract assets
            self.extract_assets(epub_path, output_dir)

            # Process chapters
            chapter_metadata = []
            chapter_slugs_used = {}

            for chapter in chapters:
                chapter_slug = self.slugify(chapter['title'])

                # Handle duplicate slugs
                if chapter_slug in chapter_slugs_used:
                    chapter_slugs_used[chapter_slug] += 1
                    chapter_slug = f"{chapter_slug}-{chapter_slugs_used[chapter_slug]}"
                else:
                    chapter_slugs_used[chapter_slug] = 1

                # Generate filename
                chapter_id = f"{chapter['order']:02d}-{chapter_slug}"
                filename = f"{chapter['order']:02d}-{book_slug}--{chapter_slug}.md"

                # Convert to Markdown
                markdown = self.html_to_markdown(
                    chapter['content'], output_dir / 'assets', chapter_slug)

                # Save Markdown file
                md_path = output_dir / filename
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)

                # Add to metadata
                chapter_metadata.append({
                    'chapter_id': chapter_id,
                    'order': chapter['order'],
                    'title': chapter['title'],
                    'markdown_file': filename
                })

            # Create meta.json
            meta = {
                'book_id': book_id,
                'title': metadata['title'],
                'author': metadata['author'],
                'chapters': chapter_metadata
            }

            meta_path = output_dir / 'meta.json'
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            if log_callback:
                log_callback(f"  ✓ Successfully converted to {output_dir}\n\n")

            # Return book entry for books.json
            return {
                'book_id': book_id,
                'title': metadata['title'],
                'author': metadata['author'],
                'description': metadata['description'],
                'meta_path': f"books_src/{book_id}/meta.json"
            }

        except Exception as e:
            if log_callback:
                log_callback(f"  ✗ Error: {str(e)}\n\n")
            return None


class EpubConverterGUI:
    """Tkinter GUI for EPUB converter"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EPUB to Markdown Converter")
        self.root.geometry("700x500")

        self.converter = EpubConverter()
        self.books_entries = []

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = tk.Label(
            self.root,
            text="EPUB to Markdown Converter",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        # Select button
        select_btn = tk.Button(
            self.root,
            text="Select EPUB Files",
            command=self.select_files,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        select_btn.pack(pady=10)

        # Log area
        log_frame = tk.Frame(self.root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(log_frame, text="Conversion Log:",
                 font=("Arial", 10)).pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update()

    def select_files(self):
        """Select EPUB files and start conversion"""
        files = filedialog.askopenfilenames(
            title="Select EPUB Files",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )

        if not files:
            return

        # Clear previous log and results
        self.log_text.delete(1.0, tk.END)
        self.books_entries = []

        self.log(f"Selected {len(files)} file(s)\n")
        self.log("="*60 + "\n\n")

        # Convert each file
        for epub_path in files:
            entry = self.converter.convert_epub(epub_path, self.log)
            if entry:
                self.books_entries.append(entry)

        # Generate clipboard content
        if self.books_entries:
            self.copy_to_clipboard()
        else:
            messagebox.showwarning("No Books Converted",
                                   "No books were successfully converted.")

    def copy_to_clipboard(self):
        """Copy books.json entries to clipboard"""
        # Format as JSON
        json_entries = []
        for entry in self.books_entries:
            json_str = json.dumps(entry, ensure_ascii=False, indent=2)
            json_entries.append(json_str)

        clipboard_content = ',\n'.join(json_entries)

        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_content)
        self.root.update()

        self.log("="*60 + "\n")
        self.log(
            f"✓ Conversion complete! {len(self.books_entries)} book(s) processed.\n")
        self.log("✓ JSON entries copied to clipboard.\n")
        self.log("\nPlease paste the following into books.json:\n")
        self.log("-"*60 + "\n")
        self.log(clipboard_content + "\n")
        self.log("-"*60 + "\n")

        messagebox.showinfo(
            "Conversion Complete",
            f"Successfully converted {len(self.books_entries)} book(s)!\n\n"
            f"JSON entries have been copied to clipboard.\n"
            f"Please paste them into books.json."
        )

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


def main():
    """主程序入口"""
    app = EpubConverterGUI()
    app.run()


if __name__ == '__main__':
    main()

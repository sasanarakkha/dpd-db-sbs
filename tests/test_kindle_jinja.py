from exporter.jinja2_env import get_jinja2_env
import os

print(f"Current working directory: {os.getcwd()}")
try:
    env = get_jinja2_env("exporter/kindle/ru_components/templates")
    template = env.get_template("ebook_ru_grammar.jinja")
    print("Successfully loaded ebook_ru_grammar.jinja")
except Exception as e:
    print(f"Error: {e}")

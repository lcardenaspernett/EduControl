from flask import Blueprint
from .main import main_bp

# Exportar el blueprint
__all__ = ['main_bp']
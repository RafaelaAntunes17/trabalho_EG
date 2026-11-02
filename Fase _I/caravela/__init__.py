"""Caravela: linguagem para descrever cenas 3D do motor Nau."""

from .semantica import analisar, verificar_semantica
from .sintaxe import parser, tokens, verificar_sintaxe

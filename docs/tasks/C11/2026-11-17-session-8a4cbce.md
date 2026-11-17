# 2026-11-17 · session · pending · C11

## Why

La revisión de C11 encontró que exigir editar la ficha y una sola entrada era frágil: el enlace a preguntas roto, ids de contexto, entradas inválidas colándose, un is-code duplicado en Python y «—» valiendo como contenido.

## Alternatives

Un hook post-commit para el sha (descartado: ensucia el árbol); detectar --amend (no hay forma fiable, se documenta el atajo task.py log); copiar is-code en Python (descartado: dos clasificaciones).

## Changed because

Se pidió en la revisión: el commit-msg exige ficha existente y entradas nuevas válidas para al menos un id; is-code.sh --list es la única clasificación; Goal, Acceptance y Why no pueden estar vacíos; path se normaliza.

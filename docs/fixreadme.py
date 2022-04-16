f = "docs/_build/markdown/readme.md"
with open(f, "r") as fp:
    txt = fp.read()
    txt = txt.replace("[\n\n!", "[!")
    txt = txt.replace(")\n\n]", ")]")
    txt = txt.replace(")[![", ")\n[![")
    txt = txt.replace(")# fcsy", ")\n\n# fcsy")

with open(f, "w") as fp:
    fp.write(txt)

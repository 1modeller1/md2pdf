import os, sys
import re
from tkinter.font import names

MERM_WIDTH = 1
MERM_SCALE = 3

def updateSection (match):
    g1 = match.group(1)
    g2 = match.group(2)
    rep = len(g1) % min_section
    return "\\" + rep*"sub" + "section{" + g2 + "}"

def updateList (match):
    g1 = match.group(1)
    g2 = match.group(2)
    rep = len(g1)
    return g2

def updateGroup (inp, func, type, i=True) -> str:
    document = ""
    level = -1
    for line in inp.splitlines():
        m = re.findall(func, line)
        if not m:
            if level > -1:
                if not i:
                    document = document[:-3] + "\n"
                document += "\\end{"+type+"}\n"
                level -= 1
            document += line + "\n"
            continue
        m = m[0]
        if len(m[0]) > level:
            document += "\\begin{"+type+"}\n"
            level += 1
        document += "\\item "*i + m[1] + r"\\"*(not i) + "\n"
        if len(m[0]) < level:
            if not i: document = document[:-3] = "\n"
            document += "\\end{"+type+"}\n"
            level -= 1
    while level >= 0:
        if not i: document = document[:-3] + "\n"
        document += "\\end{"+type+"}\n"
        level -= 1
    return document

timer = 0
def updateMerm (match):
    global timer, MERM_WIDTH
    newMerm = (r"\begin{center}" + "\n"
               r"\includegraphics[width=" + str(MERM_WIDTH) + r"\textwidth]{tmp"+str(timer)+".png}\n"
               r"\end{center}" + "\n")
    timer += 1
    return newMerm

def is_rus(ch: str) -> bool:
    return 'А' <= ch <= 'я' or ch in 'Ёё'

def inMath (match):
    gOpen = match.group(1)
    gBegin = match.group(2)
    gIn = match.group(3)
    gEnd = match.group(4)
    gClose = match.group(5)

    res = ""
    if not gOpen:
        res += "\n\n$$"
    else:
        res += "\n"
    res += "\n" + gBegin
    res += gIn
    res += gEnd + "\n"
    if not gClose:
        res += "$$\n\n"
    else:
        res += "\n"

    return res

def updateMath (match):
    group = match.group(2)
    l = len(match.group(1))
    f = r"(\\text{)?([а-яА-ЯЁё]+)"
    out = re.sub(f, makeText, group, flags=re.MULTILINE)

    out = re.sub(r"\\overline ?([^ ]+)", r"\\overline {\1}", out)
    out = re.sub(r"\\underline ?([^ ]+)", r"\\underline {\1}", out)

    # f = r"\$(\$\n)?(.*)(\\begin\{.+\}\n)([^0]*)(\n\\end{.+})(.*)(\n\$)?\$"
    # f = r"(\$\$\n)?(\\begin\{.+\}\n)([^0]*)(\n\\end{.+})(\n\$\$)?"
    # out = re.sub(f, inMath, out)
    out = re.sub(r"align", r"aligned", out)

    out = "$"*l + out + "$"*l
    return out

def makeText (match):
    if not match.group(1):
        return "\\text{" + match.group(2) + "}"
    else:
        return match.group(0)

if __name__ == "__main__":
    args = sys.argv[1:]
    name = ""
    for a in args:
        if a[0] == "-":
            continue
        name = a
        break
    if name == "":
        sys.exit("no file")
    file = open(name, "r")
    rem = True if args.count("-s") else False
    parms = open("parms.txt", "r")

    inp = parms.read()
    inp += "\n\n" + r"\begin{document}" + "\n"
    inp += file.read()

    f = r"^(#)+ "
    min_section = min((len(m.group(0)) for m in re.finditer(f, inp, flags=re.MULTILINE)), default=0) - 1

    f = r"^(#+) (.+)"
    inp = re.sub(f, updateSection, inp, flags=re.MULTILINE) # Заголовки
    # for match in re.finditer(f, inp, flags=re.MULTILINE):
    #     title = match.group(2)

    inp = updateGroup(inp, r"^(\t*)- (.*)", "itemize")
    inp = updateGroup(inp, r"^(\t*)[0-9.]+\. (.*)", "enumerate")
    inp = updateGroup(inp, r"^(\t*)>(.*)", "mdquote", False)

    f = r"\`\`\` ?merm(aid)?\n([^\`]*)\n\`\`\`"
    t = 0
    for merm in re.finditer(f, inp, flags=re.MULTILINE):    # mermaid
        tmpFile = open("tmp.mmd", "w")
        wr = merm.group(2)
        wr = wr.replace("\\n", "")
        wr = wr.replace("[", "[\"")
        wr = wr.replace("]", "\"]")
        tmpFile.write(wr)
        tmpFile.close()
        print(os.system(f"export PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome && npx mmdc -i tmp.mmd -o tmp{t}.png --scale {MERM_SCALE}"))
        t += 1
    inp = re.sub(f, updateMerm, inp)

    f = r"#(.*)"
    inp = re.sub(f, r"\#\1\\\\", inp) # Тэги или как их там

    f = r"(\$\$?)([^$]*)(\$\$?)"
    inp = re.sub(f, updateMath, inp, flags=re.MULTILINE) # Математика

    f = r"\[(.*)\]\((.*)\)"
    newF = r"\\href{\2}{\1}"
    inp = re.sub(f, newF, inp) # Ссылки

    # Таблицы
    out = ""
    box = ""
    n = 0
    doBox = False
    for line in inp.splitlines():
        if not line:
            continue
        if line[0] == "|" and line[-1] == "|":
            if doBox == False:
                n = line.count("|") - 1
                box += r"\bigskip\\" + "\n" + r"\begin{tabular}{" + "|c"*n + "|}\n" + "\\hline"
                doBox = True
            if "---" in line:
                continue
            box += line[1:-1].replace("|", " & ") + "\\\\\n" + "\\hline"
        elif doBox:
            out += box + r"\end{tabular}" + "\n"
            box = ""
            doBox = False
            out += line + "\n"
        else:
            out += line + "\n"
    if doBox:
        out += box + r"\end{tabular}" + "\n"
    inp = out

    match = False
    out = ""
    for line in inp.splitlines():
        if line[:1] == "$$":
            match = True
            continue
        elif not match and "*" in line:
            check = re.sub(r"\*\*([^*]*)\*\*", r"\\textbf{\1}", line)
            # check = re.sub(r"\*([^*]*)\*", r"\\textit{\1}", check) # <-- Подключает курсив, но у меня он отображается некорректно + нужно продумать как его убрать внутри $ math $
            out += check + "\n"
        else:
            out += line + "\n"
            match = False
    inp = out

    inp = re.sub(r"^(---)?(___)?$", r"\\medskip\n\\hrule\n\\medskip\n", inp, flags=re.MULTILINE)
    inp = inp.replace("->", "→")
    inp = inp.replace("<-", "←")

    # inp = re.sub(r"```functionplot")

    inp += "\\end{document}"
    save = open("tmp.tex", "w")
    save.write(inp)
    save.close()

    p = name.rfind(".")
    name = '"' + name[:p] + '"'

    os.system(f"xelatex -jobname={name} tmp.tex")
    if rem:
        os.system(f'rm tmp* {name}.log {name}.aux {name}.out')
    # print(inp)

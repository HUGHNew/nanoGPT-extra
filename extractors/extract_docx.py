from xml.etree.cElementTree import XML, Element
import zipfile, os
from tags import *
import utils

MULTITHREADING = True

if MULTITHREADING:
    from threading import local, Thread
    th_ref_mak = local()
    th_ref_mak.mark = False
else:
    REF_MAK = False

def mark_refences(mark:bool|None = None) -> bool:
    if mark != None:
        if MULTITHREADING:
            th_ref_mak.mark = mark
        else:
            REF_MAK = mark
    return th_ref_mak.mark if MULTITHREADING else REF_MAK

def process_p(para:Element, paragraphs:list, para_limit:int = 15):
    """process <w:p>
    :return: break current file's procedure (match References)
    Rules here:
    - #1 extract text[MAIN] p -> r -> t
    - #2 detect if `Reference` occurs[MAIN] p -> r -> t
    - ignore [CASES]:
        - #3 notation p -> r -> t (first text {`startswith` Fig})
        - #4 floating p -> r -> rPr w:position
        - #5 vertical p -> r ->..-> shape
        - #6 title-like one word paragraph: len(texts.split(" "))<20
    """
    texts = []
    ref_pat = "Reference"
    for run_block in para.iter(W_r): # error when rule#5
        # ignore rule#5 because of the para_limit
        tags = [it.tag for it in run_block]
        floating = False
        if W_rPr in tags and run_block[tags.index(W_rPr)].find(W_position) != None: floating = True # match rule #4(mark)
        # if not peek_generator(run_block.iter(W_shape)): continue # match rule #5
        if W_pict in tags: continue # match rule #5
        if W_t not in tags: continue
        text = run_block[tags.index(W_t)].text
        if len(text) == 0: continue
        if len(texts) == 0: # first word/sentence
            if utils.camel_match(text, ref_pat):
                mark_refences(True)
                return # match rule #2
            if utils.camel_match(text, "Fig"): return # match rule #3
        else:
            if texts[-1] == "R" and text == "eferences": # match rule #2 corner case
                mark_refences(True)
                return
        if floating: continue # match rule #4
        texts.append(text)

    para_content = "".join(texts)

    if utils.count_text_words(para_content) < para_limit: return # match rule #6
    para_content = utils.trim_dup_space(para_content)
    paragraphs.append(para_content) # match rule #1

def get_docx_content_fromXML(tree:Element, paragraphs:list):
    for node in tree:
        if mark_refences(): return
        if node.tag == W_tbl and len(paragraphs) > 0: paragraphs.pop()
        elif node.tag == W_p: process_p(node, paragraphs)
        else: get_docx_content_fromXML(node, paragraphs)

def get_docx_content(path, fromDocx:bool=True)->list:
    if fromDocx:
        document = zipfile.ZipFile(path)
        xml_content = document.read('word/document.xml')
        document.close()
    else:
        with open(path) as doc:
            xml_content = doc.read()
    tree = XML(xml_content)

    mark_refences(False)
    paragraphs = []
    get_docx_content_fromXML(tree, paragraphs) # DFS search
    return paragraphs

def save_docx_content(dir:str, file:str,content:list, verbose:bool=True):
    save_file = os.path.join(dir, file[:-4] + "txt")
    if verbose:
        print("saving file to:", save_file)
    with open(save_file,"w", encoding="UTF8") as sf:
        sf.write("\n\n".join(content))

def process_dir(dir:str, save_dir:str, recursive:bool=False, rewrite:bool=True):
    for file in os.listdir(dir):
        full_path = os.path.join(dir, file)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        if os.path.isdir(full_path) and recursive:
            # print("processing dir:", full_path)
            process_dir(full_path, os.path.join(save_dir, file), recursive, rewrite)
            print(full_path,"done")
        elif os.path.isfile(full_path) and file.endswith("docx"):
            save_file = os.path.join(save_dir, file[:-4] + "txt")
            if rewrite or not os.path.exists(save_dir):
                # print("saving file to:", save_file)
                with open(save_file,"w", encoding="UTF8") as sf:
                    sf.write("\n\n".join(get_docx_content(full_path)))
                # save_docx_content(save_dir, file, get_docx_content(full_path), False)


if __name__=="__main__":
    th_list = []
    dir = "docx"
    save_dir = "txt"
    recursive,rewrite = True,True
    for file in os.listdir(dir):
        full_path = os.path.join(dir, file)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        if os.path.isdir(full_path) and recursive:
            # print("processing dir:", full_path)
            if MULTITHREADING:
                th = Thread(target=process_dir,args=(full_path, os.path.join(save_dir, file), recursive, rewrite))
                th.start()
                th_list.append(th)
            else:
                process_dir(full_path, os.path.join(save_dir, file), recursive)
            print(full_path,"done")
        elif os.path.isfile(full_path) and file.endswith("docx"):
            save_file = os.path.join(save_dir, file[:-4] + "txt")
            if rewrite or not os.path.exists(save_dir):
                # print("saving file to:", save_file)
                with open(save_file,"w", encoding="UTF8") as sf:
                    sf.write("\n\n".join(get_docx_content(full_path)))
    for th in th_list:
        th.join()
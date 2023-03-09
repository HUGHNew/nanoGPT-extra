from typing import List
from xml.etree.cElementTree import XML, Element
import os, shutil

def process_default(blk:Element, checkTail:bool=True) -> str:
    rel = ""
    if blk.text:
        rel += blk.text
    if checkTail and blk.tail:
        rel += blk.tail
    return rel

def process_generally(item:Element, call:dict) -> List[str]:
    paragraph = []
    if item.tag in call:
        item_content = call[item.tag](item)
    else:
        item_content = call["_"](item)
    if item_content:
        paragraph.append(item_content)
    return paragraph

def get_p_text(p:Element) -> str:
    return " ".join(process_generally(p, {
        "list": process_list,
        "_": process_default
    }))

def process_p(p:Element, sep:str="") -> str:
    """remove labels(like italic or ref) in p
    """
    comps = [p.text] if p.text else []
    comps.extend([
        get_p_text(it)
        for it in p
    ])
    return sep.join(comps)

def process_list(lst:Element, sep:str="\n") -> str:
    return sep.join([
        process_p(p[0]) # p in list-item
        for p in lst
        if len(p) > 0
    ])

def process_sec(sec:Element, sep:str="\n") -> str:
    """sec may be nested
    """
    paragraph = []
    for item in sec:
        if item.tag == "p":
            paragraph.append(process_p(item))
        elif item.tag == "list":
            paragraph.append(process_list(item))
        elif item.tag == "sec":
            paragraph.append(process_sec(item))
    return sep.join(paragraph)

class SimpleExtractor:
    def __init__(self, chroot:str=""):
        super().__init__()
        self.root = chroot
    def extract(self, content:str|Element)->List[str]:
        if isinstance(content, Element):
            return self.fromElement(content)
        elif isinstance(content, str):
            if content.endswith("xml"): # file path
                return self.fromXmlFile(content)
            else: # treat as XML str
                return self.fromXmlStr(content)
        return []
    def fromElement(self, element:Element)-> List[str]:
        try:
            root = next(element.iter(self.root)) if self.root else element
        except:
            return []
        return [
            process_p(p)
            for p in root.iter("p")
        ]
    def fromXmlFile(self, file:str)->List[str]:
        with open(file) as f:
            content = f.read()
        return self.fromXmlStr(content)
    def fromXmlStr(self, content:str)->List[str]:
        return self.fromElement(XML(content))
    def toFile(self, content:List[str], file:str, sep:str="\n"):
        with open(file, "w", encoding="utf8") as fd:
            fd.write(sep.join(content))

class IterativeExtractor(SimpleExtractor):
    def __init__(self,chroot:str = "",post_proc=None):
        super().__init__(chroot)
        self.post_proc = post_proc
    def _post_proc(self,line:str)->str:
        return self.post_proc(line) if self.post_proc else line
    def fromElement(self, element:Element, chroot:str|None=None)-> List[str]:
        try:
            body = next(element.iter(
                chroot 
                if chroot else self.root
            ))
        except:
            return []
        paper = []
        handled = ["list", "sec", "p"]
        for blk in body:
            lines = process_generally(blk, {
                        "p": process_p,
                        "list": process_list,
                        "sec": process_sec,
                        "xref": lambda _: "",
                        "_": lambda it: it.text
                        }
                    )
            for line in lines:
                paper.append(self._post_proc(line))

            if len(blk) != 0 and blk.tag not in handled:
                for line in self.fromElement(blk, blk.tag):
                    paper.append(self._post_proc(line))

        return paper

def do_extract(extractor:SimpleExtractor, from_folder:str, to_folder:str, sep:str="\n"):
    if not os.path.exists(from_folder):
        print("folder not exist")
        return
    if not os.path.exists(to_folder):
        os.mkdir(to_folder)
    for file in os.listdir(from_folder):
        save_file = file[:-3] + "txt"
        to_save = os.path.join(to_folder,save_file)
        if os.path.exists(to_save): return
        content = extractor.fromXmlFile(os.path.join(from_folder,file))
        extractor.toFile(content,to_save, sep)


if __name__=="__main__":
    se = IterativeExtractor("body")
    print("starting unarchieve")
    for tgz in os.listdir("."):
        if os.path.isfile(tgz) and tgz.endswith("tar.gz"):
            print("unarchive:", tgz)
            shutil.unpack_archive(tgz, format="gztar")
            print(tgz, "unpacked")
            shutil.move(tgz, tgz+".done")
    print("starting extracting")
    for unpak in os.listdir("."):
        if os.path.isdir(unpak) and unpak.endswith("xxxxxx"):
            file_count = len(os.listdir(unpak))
            print("processing", unpak, "files:", file_count)
            do_extract(se, unpak, unpak[:-6], "\n\n")
            print(unpak, "extracted")

"""
edge cases: process type: truncate/pass
- References: match ^R(eference) TYPE: truncate
- Table: tbl TYPE:pass
    - table title: last p before tbl
- Image and notation: p -> r -> t(No.0 start with Fig) TYPE:pass
- floating text: p -> r -> ignore w:t if w:position in w:rPr  TYPE: pass
- ignore cases:
    - (wrong direction) p -> r -> shape TYPE:pass
    - (title or something else) ignore p if one word TYPE:pass
- Incorrect docx file
"""
_WORD_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_WORD_V = "{urn:schemas-microsoft-com:vml}"
def _add_namespace(tag:str,ns:str=_WORD_W) -> str: return ns+tag

W_p = _add_namespace('p')
W_t = _add_namespace('t')
W_r = _add_namespace('r') # <w:r> run block
W_tbl = _add_namespace("tbl") # <w:tbl>
W_rPr = _add_namespace("rPr") # <w:rPr>
W_pict = _add_namespace("pict") # <w:pict> seems the parent of <v:shape>
W_shape = _add_namespace("shape", _WORD_V) # p->r->..-><v:shape>
W_position = _add_namespace("position") # p->r->rPr->position means floating text or something

# TAG_BLOCK_LIST = [W_tbl, W_shape] # { block:blk_fn }
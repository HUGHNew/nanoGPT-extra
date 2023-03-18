import numpy as np
import tiktoken

decoder = tiktoken.get_encoding("gpt2")
array = np.memmap("./bins/val.bin", dtype=np.uint16, mode="r")
text = decoder.decode(array.tolist())
print(text)

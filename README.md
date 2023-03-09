# nanoGPT-extra

应用于 nanoGPT 的额外脚本 (主要在于数据处理)

存放路径保持与 nanoGPT 相同


- [x] drop empty lines (manually prepare data)
- data/openwebtext/prepare.py
  - chdir: data/openwebtext/
  - run: `python prepare.py`
  - use local dataset: `load_dataset("./data/new_dataset")`
  - .bin :
    - 单纯存储二进制(uint16) 将tokens用uint16表示
    - 顺序存入.bin文件 不足16位的位置用0填充
    - 每行分隔是 `tiktoken.get_encoding("gpt2").eot_token` `50256`
  - ***hint:*** [增量token](#incr-token) 数据处理与bin合并
  - [defect](#prepare):
    - `load_dataset` uses about 2.5x storage for download local dataset and cache which is useless for nanoGPT
    - `load_dataset` breaks each text into lines to read and unable to modify its default behavior
    - solution: prepare your data manually
- train.py
  - run: `torchrun --standalone --nproc_per_node=4 train.py` (eventually:`nohup torchrun --standalone --nproc_per_node=4 train.py >logs/train$time.log 2>logs/train$time.err &`)
  - `ln -s ~/anaconda/envs/gpt/include /usr/local/cuda/include` for torch 2.x compilation(`torch.compile`)
  - ***hint*** [参数设置](#param-override) train的参数设置


## prepare

使用`load_dataset` 默认行为如下:
- 下载数据到 `~/.cache/huggingface/datasets/downloads` 里面
- 创建 lock 文件
- 将处理后的数据放入 `~/.cache/huggingface/datasets/text` 里面

.cache 下最后占用存储空间可能为 原始数据大小的 2.0x-2.5x

> 似乎不会读取断点

一般而言 预计生成的 .bin 文件大小为数据集 0.3x-0.7x 如果存储紧张 建议使用手写脚本处理

## incr-token

### data process

因为 nanoGPT data prepare 处理后的结果是将文章 word embedding 后 以 uint16 存入文件(详见prepare)

> 所以可以使用增量的方式处理新的语料(直接把新数据放入openwebtext里面重新prepare也行)

对于新增的数据

> 数据可以直接用或者少量打包处理 代码直接用 prepare.py(改一下`load_dataset`里面的路径)

openwebtext 本身的格式是 tarball(.tar) 按**纯文本**处理 即新增数据格式可以是**txt**(直接将现在的文件复制过去) 也可以将多个文件打包为**tar**来存放(文件后缀改为txt)

### bin process

> 对于 prepare.py 的数据处理方式而言 多个 bin 可以直接拼接在一起(如果不shuffle)

拼接: `cat a.bin b.bin > c.bin` 按 a.bin b.bin 顺序拼接  
追加: `cat a.bin >> b.bin` 把 a.bin 拼接在 b.bin 后面

如把PMC的数据放入openwebtext文件夹生成的 .bin 跟 这放在两个文件夹生成的 .bin 拼接之后的文件是相同的 (忽略shuffle和比例分割的问题)

## param-override

train.py 默认的参数是在 import 之后的那一大块(最后一个参数是 `compile`)

它的参数重载是自己实现的(`configurator.py`) 没有使用argparse

使用方法:
- `python3 train.py --init_from=resume --out_dir=__dataset__`
- `torchrun --standalone --nproc_per_node=4 train.py --compile=False --device=cpu --min_lr=5e4 --dataset=__dataset__`

> resume 会从 `out_dir` 中获取模型参数

从参数设置来看 预计这样可以进行增量数据的训练:
`python3 train.py --init_from=resume --dataset=new_dataset`
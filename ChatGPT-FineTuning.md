# ChatGPT finetuning



[OpenAI’s blog](https://openai.com/blog/chatgpt/)

- train model using [RLHF](https://arxiv.org/pdf/2203.02155.pdf) (same methods as InstructGPT)
- supervised fine-tuning(SFT)

## materials

- [FT GPT-3 vs. ChatGPT](https://www.allabtai.com/chatgpt-vs-gpt-3-fine-tuning-the-ultimate-comparison/):
  - GPT-3 微调比 ChatGPT 更通用
  - ChatGPT使用记忆模块来帮助理解上下文
  - `ChatGPT` 不需要微调 可以通过 prompt-engineering 获得更好的效果
  - fine-tuning 之后的 GPT-3 可能效果更差

- [Fine-Tuning LLMs with LoRA](https://ai.plainenglish.io/creating-your-own-chatgpt-a-guide-to-fine-tuning-llms-with-lora-d7817b77fac0)(an example with Flan-T5XXL): use LoRA to accelerate fine-tuning
- [ChatGPT Resources](https://gist.github.com/veekaybee/6f8885e9906aa9c5408ebe5c7e870698)
  - GPT-3 data
    - Books1: [BookCorpus](https://arxiv.org/pdf/2105.05241.pdf)
    - Books2: libgen(maybe)
    - some mystery books [here](https://the-eye.eu/public/AI/pile_preliminary_components/)
      - github.tar 106G
      - openwebtext2.jsonl.zst.tar 27G
      - stackexchange_dataset.tar 34G
      - PMC_extracts.tar.gz 26G

![Training-Data](https://user-images.githubusercontent.com/3837836/206871628-b2a1e151-4585-40cb-aaae-742e1088d442.png "GPT-3 Training Data")



## See more

prompt-engineering:

- [examples](https://www.allabtai.com/chatgpt-prompt-engineering-sequence-prompt/)
- [tips](https://www.allabtai.com/the-5-best-prompt-engineering-tips-for-beginners/)

[RLPROMPT: Optimizing Discrete Text Prompts with Reinforecement Learning](https://arxiv.org/pdf/2205.12548.pdf)

[TRL](https://github.com/lvwerra/trl) - Transformer Reinforcement Learning: follows [**Fine-Tuning Language Models from Human Preferences**](**Fine-Tuning Language Models from Human Preferences**)

## [GPT-3 fine-tuning][GPT3FT]

### Data formatting

```json
{
    "prompt": "(input) 详细指令 or 多个示例 P_SEP",
    "completion": " (output) C_SEP" // start with a whitespace (due to GPT `tokenization`)
}
```

examples:

```json
// sentiment analysis
{"prompt":"Overjoyed with the new iPhone! ->", "completion":" positive"}
{"prompt":"@lakers disappoint for a third straight night https://t.co/38EFe43 ->", "completion":" negative"}

// classifier
{"prompt":"Company: BHFF insurance\nProduct: allround insurance\nAd:One stop shop for all your insurance needs!\nSupported:", "completion":" yes"}
{"prompt":"Company: Loft conversion specialists\nProduct: -\nAd:Straight teeth in weeks!\nSupported:", "completion":" no"}

// conditional generation
// prompt + completion <= 2048 tokens
{"prompt":"<Product Name>\n<Wikipedia description>\n\n###\n\n", "completion":" <engaging ad> END"}
{"prompt":"Samsung Galaxy Feel\nThe Samsung Galaxy Feel is an Android smartphone developed by Samsung Electronics exclusively for the Japanese market. The phone was released in June 2017 and was sold by NTT Docomo. It runs on Android 7.0 (Nougat), has a 4.7 inch display, and a 3000 mAh battery.\nSoftware\nSamsung Galaxy Feel runs on Android 7.0 (Nougat), but can be later updated to Android 8.0 (Oreo).\nHardware\nSamsung Galaxy Feel has a 4.7 inch Super AMOLED HD display, 16 MP back facing and 5 MP front facing cameras. It has a 3000 mAh battery, a 1.6 GHz Octa-Core ARM Cortex-A53 CPU, and an ARM Mali-T830 MP1 700 MHz GPU. It comes with 32GB of internal storage, expandable to 256GB via microSD. Aside from its software and hardware specifications, Samsung also introduced a unique a hole in the phone's shell to accommodate the Japanese perceived penchant for personalizing their mobile phones. The Galaxy Feel's battery was also touted as a major selling point since the market favors handsets with longer battery life. The device is also waterproof and supports 1seg digital broadcasts using an antenna that is sold separately.\n\n###\n\n", "completion":"Looking for a smartphone that can do it all? Look no further than Samsung Galaxy Feel! With a slim and sleek design, our latest smartphone features high-quality picture and video capabilities, as well as an award winning battery life. END"}
```



show case

```bash
$ cat data/ft/ft/ms_1718.txt
Answer the following question "Peyronie's disease for member with dupuytren's contractures?" The answer is:Peyronie’s disease also have Dupuytren’s contracture, a connective tissue disorder that causes scar tissue to harden on the palm of the hand. This causes fingers to curve, much like the penis curves in Peyronie’s disease.
```



```json
{
    "prompt": "Peyronie's disease for member with dupuytren's contractures? Answer:",
    "completion": "Peyronie’s disease also have Dupuytren’s contracture, a connective tissue disorder that causes scar tissue to harden on the palm of the hand. This causes fingers to curve, much like the penis curves in Peyronie’s disease."
}
```



[GPT3FT]: https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset

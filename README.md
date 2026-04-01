# colab-slm-playground

Run Small Language Model (SLM) inference and chat UIs directly inside Google Colab — no Flask, no tunnels. The chat UI bridges JS to Python via `google.colab.kernel.invokeFunction`, so everything runs inside the notebook with no external server.

## Notebooks

| Notebook | Runtime | Description | Open |
|---|---|---|---|
| [LFM2.5-350M Chatbot](lfm2_chatbot_colab.ipynb) | CPU | Chat UI for [LiquidAI/LFM2.5-350M-ONNX](https://huggingface.co/LiquidAI/LFM2.5-350M-ONNX). Uses raw ONNX Runtime — required because LFM2 has a non-standard KV-cache layout. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jonasneves/colab-slm-playground/blob/main/lfm2_chatbot_colab.ipynb) |
| [Trending ONNX Chatbot](trending_onnx_chatbot_colab.ipynb) | CPU | Fetches trending ONNX `text-generation` models, lets you pick one, and runs a chat UI. Uses Optimum — works with standard exported models. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jonasneves/colab-slm-playground/blob/main/trending_onnx_chatbot_colab.ipynb) |
| [Trending GGUF Chatbot](trending_gguf_chatbot_colab.ipynb) | CPU | Fetches trending GGUF models, lets you pick a model and quantization variant. Uses llama-cpp-python. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jonasneves/colab-slm-playground/blob/main/trending_gguf_chatbot_colab.ipynb) |
| [Trending PyTorch Chatbot](trending_pytorch_chatbot_colab.ipynb) | T4 GPU | Fetches trending `text-generation` models and runs them via `transformers`. Supports fp16 and 4-bit (bitsandbytes). Requires a GPU runtime. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jonasneves/colab-slm-playground/blob/main/trending_pytorch_chatbot_colab.ipynb) |

> [!TIP]
> **Students get Colab Pro free for 1 year.** That means GPU access, more memory, and longer runtimes at no cost. [Claim it here.](https://blog.google/products-and-platforms/products/education/colab-higher-education/)
>
> More free tools for students: [student-benefits.github.io/benefits](https://student-benefits.github.io/benefits/)

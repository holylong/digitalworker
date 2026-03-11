windows原生安装

set NODE_LLAMA_CPP_SKIP_DOWNLOAD=true

$env:NODE_LLAMA_CPP_SKIP_DOWNLOAD="true"
iwr -useb https://openclaw.ai/install.ps1 | iex

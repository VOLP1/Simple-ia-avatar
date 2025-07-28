Avatar Falante com IA (Python, Pygame, Gemini e ElevenLabs)
Este projeto apresenta um avatar de robô 2D interativo que utiliza reconhecimento de fala, inteligência artificial conversacional e síntese de voz para criar uma experiência de diálogo em tempo real.

Funcionalidades
Reconhecimento de Voz em Tempo Real: Ouve o microfone do usuário para capturar a fala.

Inteligência Conversacional: Utiliza a API do Google Gemini para entender o que foi dito e gerar respostas inteligentes e contextuais.

Síntese de Voz Realista: Converte o texto gerado pela IA em uma voz natural usando a API da ElevenLabs.

Animação de Sincronia Labial:

Modo Ideal: Utiliza dados de alinhamento da API da ElevenLabs para uma sincronia labial precisa com cada caractere falado.

Modo de Fallback Inteligente: Caso os dados de alinhamento não sejam recebidos, o programa analisa o volume do áudio em tempo real e anima a boca de acordo, criando um efeito dinâmico e convincente.

Feedback Visual: O avatar muda a cor dos olhos para indicar seu estado atual (ouvindo, pensando, falando ou erro).

Arquitetura e Tecnologias
Linguagem: Python 3

Gráficos e Janela: Pygame

Reconhecimento de Fala: speech_recognition e pyaudio

Inteligência Artificial: Google Gemini (google-generativeai)

Síntese de Voz: ElevenLabs API (elevenlabs)

Análise de Áudio (Fallback): pydub e numpy

Dependência Externa: FFmpeg (para processamento de áudio)

Guia de Instalação e Execução
Siga estes passos para configurar e rodar o projeto no seu ambiente Windows.

1. Pré-requisitos
Antes de começar, garanta que você tem:

Python 3.8 ou superior instalado.

Um microfone funcionando e configurado no Windows.

Uma chave de API da ElevenLabs.

Uma chave de API do Google Gemini.

2. Instalação do FFmpeg (Dependência Crucial)
Esta biblioteca é necessária para a análise de áudio da animação de fallback.

Baixe o FFmpeg: Vá para https://www.gyan.dev/ffmpeg/builds/, encontre a seção "release builds" e baixe o arquivo ffmpeg-release-essentials.zip.

Extraia os Arquivos: Extraia o conteúdo para um local permanente. Recomendamos mover a pasta extraída para C:\ e renomeá-la para ffmpeg, resultando em C:\ffmpeg.

Adicione ao Path do Windows:

No menu Iniciar, pesquise por "variáveis de ambiente" e abra "Editar as variáveis de ambiente do sistema".

Clique em "Variáveis de Ambiente...".

Na seção "Variáveis do sistema", selecione a variável Path e clique em "Editar...".

Clique em "Novo" e adicione o caminho para a pasta bin do FFmpeg: C:\ffmpeg\bin.

Clique "OK" em todas as janelas para salvar.

Verifique: Feche e abra um novo terminal (PowerShell/CMD) e digite ffmpeg -version. Se informações da versão aparecerem, a instalação foi um sucesso.

3. Configuração do Projeto Python
Crie a pasta do projeto: Crie uma pasta, entre nela e salve o código do avatar como main.py.

Crie e ative um ambiente virtual (recomendado):

PowerShell

python -m venv venv
.\venv\Scripts\Activate
Instale as bibliotecas Python: Com o ambiente virtual ativado, instale todas as dependências com o seguinte comando:

PowerShell

pip install pygame elevenlabs google-generativeai speechrecognition pyaudio requests numpy pydub
4. Configuração das Chaves de API
Este projeto usa variáveis de ambiente para carregar suas chaves de API de forma segura. Abra um terminal na pasta do seu projeto e execute os seguintes comandos, substituindo "sua_chave_aqui" pelas suas chaves reais.

PowerShell

# Chave da API da ElevenLabs
$env:ELEVENLABS_API_KEY="sua_chave_elevenlabs_aqui"

# Chave da API do Google Gemini
$env:GOOGLE_API_KEY="sua_chave_google_aqui"
Importante: Essas variáveis de ambiente são válidas apenas para a sessão atual do terminal. Se você fechar o terminal, precisará defini-las novamente antes de executar o script.

5. Executar o Avatar
Com tudo configurado, execute o script:

PowerShell

python main.py
Controles
Pressione Barra de Espaço: Para ativar o microfone e começar a falar.

Pressione Q: Para fechar a aplicação.

Solução de Problemas (Troubleshooting)
ERRO: Couldn't find ffmpeg... / A boca não se mexe.

Causa: O FFmpeg não foi instalado ou o seu caminho não foi adicionado corretamente às variáveis de ambiente do Windows.

Solução: Refaça o Passo 2 do guia de instalação com atenção e verifique a instalação com o comando ffmpeg -version em um novo terminal.

ERRO: Erro HTTP: 401... ou erros relacionados a permissão.

Causa: Sua chave de API está incorreta ou não foi definida corretamente como uma variável de ambiente.

Solução: Verifique se você copiou as chaves corretamente e se executou os comandos $env:... no mesmo terminal em que está rodando o script.

ERRO: Erro no microfone ou Não entendi. Tente novamente.

Causa: O microfone não foi detectado ou não está capturando áudio claramente.

Solução: Verifique se seu microfone está conectado, selecionado como o dispositivo de gravação padrão no Windows e se o volume de entrada está adequado.

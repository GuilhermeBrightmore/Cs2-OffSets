# CS2 Dumper Automation

Este projeto automatiza o processo de geração, processamento e versionamento de offsets para CS2 utilizando cs2-dumper.exe. O script Python executa o dumper, processa os arquivos gerados para extrair informações de offsets, e faz o commit automático do arquivo JSON resultante para um repositório GitHub.

## Características

- Executa automaticamente o cs2-dumper.exe com parâmetros configuráveis
- Limpa e recria o diretório de saída antes de cada execução
- Extrai offsets de namespaces e variáveis de arquivos .hpp
- Gera três arquivos de saída:
  - `offsets.json`: Arquivo JSON com todos os offsets encontrados
  - `offsets.hpp`: Estruturas C++ para os offsets (sem valores definidos)
  - `set_offsets.cpp`: Código para atribuição dos offsets via função findOffsetByName
- Faz commit automático do arquivo JSON para um repositório GitHub

## Requisitos

- Python 3.6 ou superior
- CS2 Dumper (cs2-dumper.exe)
- Bibliotecas Python:
  - PyGithub
  - shutil (padrão)
  - os (padrão)
  - subprocess (padrão)
  - json (padrão)
  - re (padrão)
  - glob (padrão)
  - sys (padrão)
  - datetime (padrão)
  - time (padrão)

## Instalação

1. Clone este repositório:
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

2. Instale as dependências necessárias:
```bash
pip install PyGithub
```

3. Configure as variáveis no início do script conforme suas necessidades.

## Configuração

Antes de executar o script, é necessário configurar algumas variáveis no código:

```python
# Configurações
OUTPUT_DIR = "D:\\Baimless\\Salamundengo\\A2X Generate Files"  # Diretório de saída
CS2_DUMPER_PATH = "cs2-dumper.exe"                          # Caminho para o cs2-dumper.exe
GITHUB_TOKEN = "seu_token_github_aqui"                      # Token de acesso ao GitHub
REPO_NAME = "seu_usuario/seu_repositorio"                   # Formato: "usuario/nome_do_repo"
JSON_FILE_PATH = "offsets.json"                             # Arquivo a ser enviado ao GitHub
COMMIT_MESSAGE = "Atualização automática de offsets via script Python"  # Mensagem do commit
```

### Como obter um token do GitHub

1. Acesse as configurações do GitHub em `Settings` > `Developer settings` > `Personal access tokens` > `Tokens (classic)`
2. Clique em `Generate new token`
3. Dê um nome ao token e selecione o escopo `repo` para acesso completo ao repositório
4. Clique em `Generate token` e copie o token gerado
5. Cole o token na variável `GITHUB_TOKEN` do script

## Uso

Para executar o script:

```bash
python cs2_dumper_automation.py
```

### Fluxo de Execução

1. O script exclui e recria o diretório de saída especificado
2. Executa o cs2-dumper.exe com os parâmetros `-f hpp` e `-o` apontando para o diretório de saída
3. Processa todos os arquivos .hpp gerados para extrair informações de offsets
4. Gera os arquivos offsets.json, offsets.hpp e set_offsets.cpp
5. Faz o commit do arquivo offsets.json para o repositório GitHub configurado

## Estrutura de Funcionamento

### 1. Preparação do Ambiente
```python
# Exclui e recria o diretório de saída
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)
```

### 2. Execução do CS2 Dumper
```python
# Executa o cs2-dumper.exe com os parâmetros necessários
cmd = [CS2_DUMPER_PATH, "-f", "hpp", "-o", OUTPUT_DIR]
result = subprocess.run(cmd, capture_output=True, text=True)
```

### 3. Processamento dos Arquivos
```python
# Processar todos os arquivos .hpp
all_offsets = process_all_cpp_files(OUTPUT_DIR)
```

### 4. Geração dos Arquivos de Saída
```python
# Gera o arquivo JSON
output_json = os.path.join(os.getcwd(), JSON_FILE_PATH)
save_offsets_to_json(all_offsets, output_json)

# Gera o arquivo HPP
output_hpp = os.path.join(os.getcwd(), 'offsets.hpp')
with open(output_hpp, 'w', encoding='utf-8') as hpp_file:
    hpp_file.write(generate_hpp(all_offsets))

# Gera o arquivo C++ para as atribuições
output_cpp = os.path.join(os.getcwd(), 'set_offsets.cpp')
generate_cpp_offset_code(output_json, output_cpp)
```

### 5. Commit para o GitHub
```python
# Fazer o commit do arquivo JSON para o GitHub
commit_result = commit_to_github(output_json)
```

## Estrutura dos Arquivos Gerados

### offsets.json
```json
{
    "namespace1": {
        "variable1": "0x12345678",
        "variable2": "0x87654321"
    },
    "namespace2": {
        "variable1": "0xABCDEF12"
    }
}
```

### offsets.hpp
```cpp
inline struct namespace1Offsets {
    DWORD variable1;
    DWORD variable2;
} namespace1;

inline struct namespace2Offsets {
    DWORD variable1;
} namespace2;
```

### set_offsets.cpp
```cpp
// Atribuições para namespace1
// namespace1 Offsets
namespace1.variable1 = findOffsetByName(j, "namespace1", "variable1");
namespace1.variable2 = findOffsetByName(j, "namespace1", "variable2");

// Atribuições para namespace2
// namespace2 Offsets
namespace2.variable1 = findOffsetByName(j, "namespace2", "variable1");
```

## Agendamento de Execução

Para executar o script automaticamente em intervalos regulares:

### No Windows (usando Task Scheduler):
1. Crie um arquivo .bat com o conteúdo:
```batch
@echo off
cd /d "caminho\para\seu\script"
python cs2_dumper_automation.py
```

2. Abra o Task Scheduler (Agendador de Tarefas)
3. Crie uma nova tarefa com o trigger desejado (diário, semanal, etc.)
4. Configure a ação para executar o arquivo .bat criado

### No Linux (usando cron):
1. Abra o crontab:
```bash
crontab -e
```

2. Adicione uma linha como:
```
0 0 * * * cd /caminho/para/seu/script && python3 cs2_dumper_automation.py
```
(executa diariamente à meia-noite)

## Solução de Problemas

### O script não encontra o cs2-dumper.exe
- Verifique se o caminho para o executável está correto
- Tente usar o caminho absoluto para o executável

### Erro de conexão com o GitHub
- Verifique se o token está correto e tem as permissões necessárias
- Confirme se há conexão com a internet

### Diretório de saída não está sendo criado
- Certifique-se de que o script tem permissões para criar diretórios no local especificado
- Verifique se o caminho não contém caracteres especiais que possam causar problemas

### Nenhum offset está sendo encontrado
- Verifique se o cs2-dumper.exe está gerando os arquivos .hpp corretamente
- Inspecione os arquivos .hpp manualmente para confirmar a estrutura esperada

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Aviso de Segurança

**Importante**: Nunca compartilhe seu token do GitHub ou o inclua em repositórios públicos. Use variáveis de ambiente ou arquivos de configuração separados que não sejam versionados para armazenar informações sensíveis.
